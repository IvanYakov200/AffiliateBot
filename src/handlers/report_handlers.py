from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config.config import *
from database.database import *
from services.appsflyer_service import get_appsflyer_raw_data_custom, get_post_attribution_report
from utils.report_utils import generate_report
from handlers.offer_handlers import is_admin
from io import BytesIO
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

async def start_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Admin rights required")
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton("📥 Installs", callback_data="report_installs")],
        [InlineKeyboardButton("🎮 In-App Events", callback_data="report_events")],
        [InlineKeyboardButton("📮 Post-attribution", callback_data="report_post_attribution")]
    ]   

    await update.message.reply_text(
        "📊 Select report type:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return REPORT_TYPE_SELECT

async def select_report_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Исправляем разбор типа отчета
    report_type = query.data.split("_")[1]
    if report_type == "post":
        report_type = "post_attribution"
    
    context.user_data['report_type'] = report_type
    logger.info(f"Selected report type: {report_type}")

    if report_type == 'events':
        event_keyboard = [
            [InlineKeyboardButton("🚀 Use offer event", callback_data="use_offer_event")],
            [InlineKeyboardButton("✏️ Input manually", callback_data="input_custom_event")]
        ]
        await query.edit_message_text(
            "📌 Select event source:",
            reply_markup=InlineKeyboardMarkup(event_keyboard)
        )
        return REPORT_EVENT_INPUT
    else:
        await query.edit_message_text("📅 Enter dates in format YYYY-MM-DD YYYY-MM-DD\nExample: 2024-01-01 2024-01-31")
        return REPORT_DATES

async def handle_event_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "input_custom_event":
        await query.edit_message_text("📝 Enter event name (e.g., purchase, level_complete):")
        return REPORT_EVENT_NAME
    else:
        context.user_data['event_source'] = 'offer'
        await query.edit_message_text("📅 Enter dates in format YYYY-MM-DD YYYY-MM-DD")
        return REPORT_DATES

async def process_event_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['event_name'] = update.message.text.strip()

    keyboard = [
        [InlineKeyboardButton("✅ Use all fields", callback_data="all_fields"),
         InlineKeyboardButton("🚫 No additional fields", callback_data="no_fields")],
        [InlineKeyboardButton("✏️ Specify fields", callback_data="custom_fields")]
    ]

    await update.message.reply_text(
        "📋 Choose additional fields option:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return REPORT_FIELDS_SELECT

async def handle_fields_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    choice = query.data
    if choice == "custom_fields":
        await query.edit_message_text("📝 Enter additional fields (comma-separated):")
        return REPORT_CUSTOM_FIELDS
    elif choice == "no_fields":
        context.user_data['additional_fields'] = None
        await query.edit_message_text("📅 Enter dates in format YYYY-MM-DD YYYY-MM-DD")
        return REPORT_DATES
    else:
        context.user_data['additional_fields'] = 'all'
        await query.edit_message_text("📅 Enter dates in format YYYY-MM-DD YYYY-MM-DD")
        return REPORT_DATES

async def process_custom_fields(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['additional_fields'] = update.message.text.strip()
    await update.message.reply_text("📅 Enter dates in format YYYY-MM-DD YYYY-MM-DD")
    return REPORT_DATES

async def process_dates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dates = update.message.text.split()
    if len(dates) != 2:
        await update.message.reply_text("❌ Invalid format. Enter two dates separated by space")
        return REPORT_DATES

    try:
        from_date = datetime.strptime(dates[0], "%Y-%m-%d")
        to_date = datetime.strptime(dates[1], "%Y-%m-%d")
        if from_date > to_date:
            await update.message.reply_text("❌ 'To' date must be after 'From' date")
            return REPORT_DATES
        context.user_data['date_from'], context.user_data['date_to'] = dates
    except ValueError:
        await update.message.reply_text("❌ Invalid date format. Use YYYY-MM-DD")
        return REPORT_DATES

    offers = get_all_offers()
    if not offers:
        await update.message.reply_text("❌ No available offers")
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton(f"{offer[1]}", callback_data=f"report_offer_{offer[0]}")]
        for offer in offers
    ]
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="report_cancel")])

    await update.message.reply_text(
        "📋 Select offer from list:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return REPORT_SELECT_OFFER

async def select_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "report_cancel":
        await query.edit_message_text("❌ Report generation cancelled")
        return ConversationHandler.END
        
    offer_id = int(query.data.split('_')[2])
    offer = get_offer_details(offer_id)
    
    if not offer:
        await query.edit_message_text("❌ Offer not found")
        return ConversationHandler.END
        
    try:
        # Отправляем сообщение о начале обработки
        processing_message = await query.edit_message_text("⏳ Processing your report... This may take a few moments.")
        
        report_type = context.user_data.get('report_type')
        appsflyer_offer_id = offer[10]
        event_name = offer[11]
        
        logger.info(f"Generating report of type: {report_type}")
        logger.info(f"Offer ID: {offer_id}, AppsFlyer ID: {appsflyer_offer_id}")
        
        params = {
            'from': context.user_data['date_from'],
            'to': context.user_data['date_to'],
            'app_id': appsflyer_offer_id
        }
        
        logger.info(f"Report parameters: {params}")
        
        csv_data = None
        
        if report_type == 'events':
            params['event_name'] = context.user_data.get('event_name', event_name)
            endpoint = f"{APPSFLYER_BASE_URL}/{appsflyer_offer_id}/in_app_events_report/v5"
            logger.info(f"Events endpoint: {endpoint}")
            csv_data = get_appsflyer_raw_data_custom(endpoint, params)
        elif report_type == 'installs':
            endpoint = f"{APPSFLYER_BASE_URL}/{appsflyer_offer_id}/installs_report/v5"
            logger.info(f"Installs endpoint: {endpoint}")
            csv_data = get_appsflyer_raw_data_custom(endpoint, params)
        elif report_type == 'post_attribution':
            logger.info("Getting post-attribution report")
            csv_data = get_post_attribution_report(params)
            
        if not csv_data:
            logger.warning(f"No data received for report type: {report_type}")
            await processing_message.edit_text(f"⚠️ No data for period {params['from']} - {params['to']}")
            return ConversationHandler.END
            
        logger.info(f"Successfully received data, size: {len(csv_data)} bytes")
        
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=BytesIO(csv_data),
            filename=f"{report_type}_{params['from']}_to_{params['to']}.csv",
            caption=f"📊 Report for: {offer[1]}\nType: {report_type}"
        )
        
        # Удаляем сообщение о процессе после успешной отправки
        await processing_message.delete()
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        await processing_message.edit_text("❌ Error generating report")
        
    return ConversationHandler.END 
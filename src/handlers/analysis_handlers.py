from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config.config import *
from database.database import *
from services.appsflyer_service import get_appsflyer_raw_data_custom
from utils.report_utils import (
    generate_conversion_analysis,
    generate_revenue_forecast,
    generate_trend_analysis
)
from datetime import datetime

async def start_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📈 Conversion", callback_data="analysis_conversion")],
        [InlineKeyboardButton("🔮 Revenue Forecast", callback_data="analysis_forecast")],
        [InlineKeyboardButton("📉 Trends", callback_data="analysis_trends")]
    ]
    await update.message.reply_text(
        "📊 Select analysis type:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ANALYSIS_TYPE

async def process_analysis_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['analysis_type'] = query.data.split('_')[1]
    
    offers = get_all_offers()
    keyboard = [
        [InlineKeyboardButton(offer[1], callback_data=f"analysis_offer_{offer[0]}")]
        for offer in offers
    ]
    await query.edit_message_text(
        "Select offer for analysis:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ANALYSIS_OFFER_SELECT

async def select_analysis_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    offer_id = int(query.data.split('_')[2])
    context.user_data['analysis_offer_id'] = offer_id
    
    await query.edit_message_text("📅 Enter dates in format YYYY-MM-DD YYYY-MM-DD\nExample: 2024-01-01 2024-01-31")
    return ANALYSIS_DATES

async def process_analysis_dates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dates = update.message.text.split()
    if len(dates) != 2:
        await update.message.reply_text("❌ Invalid format. Enter two dates separated by space")
        return ANALYSIS_DATES

    try:
        from_date = datetime.strptime(dates[0], "%Y-%m-%d")
        to_date = datetime.strptime(dates[1], "%Y-%m-%d")
        if from_date > to_date:
            await update.message.reply_text("❌ 'To' date must be after 'From' date")
            return ANALYSIS_DATES
            
        context.user_data['analysis_dates'] = {
            'from': dates[0],
            'to': dates[1]
        }
        
        keyboard = [
            [InlineKeyboardButton("🔍 Specify source", callback_data="specific_source")],
            [InlineKeyboardButton("🌐 All sources", callback_data="all_sources")]
        ]
    
        await update.message.reply_text(
            "Select traffic source:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ANALYSIS_SOURCE_CHOICE

    except ValueError:
        await update.message.reply_text("❌ Invalid date format. Use YYYY-MM-DD")
        return ANALYSIS_SOURCE_CHOICE

async def handle_source_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "specific_source":
        await query.edit_message_text("📢 Enter source name (e.g., facebook, google_ads):")
        return ANALYSIS_MEDIA_SOURCE
    else:
        context.user_data['media_source'] = 'all'
        return await perform_analysis(update, context)

async def process_media_source(update: Update, context: ContextTypes.DEFAULT_TYPE):
    media_source = update.message.text.strip()
    context.user_data['media_source'] = media_source
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirm", callback_data="confirm_media_source")],
        [InlineKeyboardButton("✏️ Change", callback_data="change_media_source")]
    ]
    
    await update.message.reply_text(
        f"📢 Traffic source: {media_source}\n"
        "Confirm or change:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ANALYSIS_PARAMS

async def handle_media_source_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "change_media_source":
        await query.edit_message_text("Enter traffic source (e.g., facebook, google_ads):")
        return ANALYSIS_MEDIA_SOURCE
    
    return await perform_analysis(update, context)

async def perform_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    offer_id = context.user_data.get('analysis_offer_id')
    analysis_dates = context.user_data.get('analysis_dates')
    analysis_type = context.user_data.get('analysis_type')
    media_source = context.user_data.get('media_source', 'all')

    if not all([offer_id, analysis_dates, analysis_type]):
        await query.edit_message_text("❌ Analysis data lost")
        return ConversationHandler.END

    offer = get_offer_details(offer_id)
    if not offer or not offer[10] or not offer[11]:
        await query.edit_message_text("❌ Offer not found or missing AppsFlyer ID/Event Name")
        return ConversationHandler.END

    try:
        params = {
            'app_id': offer[10],
            'from': analysis_dates['from'],
            'to': analysis_dates['to'],
            'media_source': media_source if media_source != 'all' else None
        }

        if analysis_type == 'conversion':
            # Get installs and events data
            installs_endpoint = f"{APPSFLYER_BASE_URL}/{offer[10]}/installs_report/v5"
            events_endpoint = f"{APPSFLYER_BASE_URL}/{offer[10]}/in_app_events_report/v5"
            
            installs_data = get_appsflyer_raw_data_custom(installs_endpoint, params)
            events_params = params.copy()
            events_params['event_name'] = offer[11]
            events_data = get_appsflyer_raw_data_custom(events_endpoint, events_params)
            
            graph = generate_conversion_analysis(
                installs_data.decode("utf-8"),
                events_data.decode("utf-8"),
                offer[1],
                (analysis_dates['from'], analysis_dates['to'])
            )

        elif analysis_type == 'forecast':
            events_endpoint = f"{APPSFLYER_BASE_URL}/{offer[10]}/in_app_events_report/v5"
            params['event_name'] = offer[11]
            events_data = get_appsflyer_raw_data_custom(events_endpoint, params)
            
            graph = generate_revenue_forecast(
                events_data.decode("utf-8"),
                offer[3],  # payout
                (analysis_dates['from'], analysis_dates['to'])
            )

        elif analysis_type == 'trends':
            installs_endpoint = f"{APPSFLYER_BASE_URL}/{offer[10]}/installs_report/v5"
            installs_data = get_appsflyer_raw_data_custom(installs_endpoint, params)
            
            graph = generate_trend_analysis(
                installs_data.decode("utf-8"),
                (analysis_dates['from'], analysis_dates['to']),
                offer[1]
            )

        source_info = f"Source: {media_source}" if media_source != 'all' else "All sources"
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=graph,
            caption=f"📊 Analysis Result ({analysis_type})\n"
                    f"Offer: {offer[1]}\n"
                    f"Source: {source_info}\n"
                    f"Period: {analysis_dates['from']} - {analysis_dates['to']}"
        )

    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        await query.edit_message_text("❌ Error performing analysis")

    return ConversationHandler.END 
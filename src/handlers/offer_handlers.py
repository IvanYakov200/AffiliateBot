from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config.config import *
from database.database import *
import validators

async def is_admin(user_id: int) -> bool:
    """Check if user has admin rights"""
    return get_user_role(user_id) == 'admin'

async def start_add_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 You don't have permission to perform this action.")
        return ConversationHandler.END

    await update.message.reply_text("Let's add a new offer. First, enter the offer name.")
    return OFFER_NAME

async def process_offer_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['offer_name'] = update.message.text
    await update.message.reply_text("Enter offer description:")
    return OFFER_DESC

async def process_offer_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['offer_desc'] = update.message.text
    await update.message.reply_text("Enter payout amount (USD):")
    return OFFER_PAYOUT

async def process_offer_payout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        payout = float(update.message.text)
        context.user_data['offer_payout'] = payout
        await update.message.reply_text("Enter target GEO countries (comma-separated):")
        return OFFER_GEO
    except ValueError:
        await update.message.reply_text("Please enter a valid number for payout. Try again:")
        return OFFER_PAYOUT

async def process_offer_geo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['offer_geo'] = update.message.text
    await update.message.reply_text("Enter vertical (e.g., Games, Finance, E-commerce):")
    return OFFER_VERTICAL

async def process_offer_vertical(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['offer_vertical'] = update.message.text
    await update.message.reply_text("Enter KPI requirements:")
    return OFFER_KPI

async def process_offer_kpi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['offer_kpi'] = update.message.text
    await update.message.reply_text("Enter tracker:")
    return OFFER_TRACKER

async def process_offer_tracker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['offer_tracker'] = update.message.text
    await update.message.reply_text("Enter anti-fraud system:")
    return OFFER_ANTIFRAUD

async def process_offer_antifraud(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['offer_antifraud'] = update.message.text
    await update.message.reply_text("Enter AppsFlyer Offer ID:")
    return OFFER_APPSFLYER_ID

async def process_appsflyer_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['appsflyer_offer_id'] = update.message.text
    await update.message.reply_text("Enter event name:")
    return OFFER_EVENT_NAME

async def process_offer_event_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['event_name'] = update.message.text
    offer_data = {
        'name': context.user_data['offer_name'],
        'description': context.user_data['offer_desc'],
        'payout': context.user_data['offer_payout'],
        'geo': context.user_data['offer_geo'],
        'vertical': context.user_data['offer_vertical'],
        'kpi': context.user_data['offer_kpi'],
        'tracker': context.user_data['offer_tracker'],
        'antifraud': context.user_data['offer_antifraud'],
        'appsflyer_offer_id': context.user_data['appsflyer_offer_id'],
        'event_name': context.user_data['event_name']
    }
    add_offer_to_db(offer_data)
    await update.message.reply_text("✅ Offer successfully added!")
    return ConversationHandler.END

async def list_offers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    role = get_user_role(user_id)
    offers = get_all_offers()

    if not offers:
        await update.message.reply_text("No active offers.")
        return

    keyboard = []
    for offer in offers:
        btn_text = f"{offer[1]} (${offer[3]})"
        if role == 'admin':
            row = [
                InlineKeyboardButton(btn_text, callback_data=f"offer_view_{offer[0]}"),
                InlineKeyboardButton("✏️ Edit", callback_data=f"offer_edit_{offer[0]}"),
                InlineKeyboardButton("❌ Delete", callback_data=f"offer_delete_{offer[0]}")
            ]
        else:
            row = [InlineKeyboardButton(btn_text, callback_data=f"offer_view_{offer[0]}")]
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        '📋 Active Offers:',
        reply_markup=reply_markup
    )

async def show_offer_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    offer_id = int(query.data.split('_')[2])
    offer = get_offer_details(offer_id)

    if offer:
        text = f"""
        📌 *{offer[1]}*
        💰 Payout: ${offer[3]}
        🌍 GEO: {offer[4]}
        📊 Vertical: {offer[5]}
        ✅ *KPI*:
        {offer[6]}
        🔗 *Tracker*: {offer[7]}
        🛡️ *Anti-fraud*: {offer[8]}
        Event: {offer[11]}
        """
        await query.edit_message_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("← Back to offers", callback_data="offers_list")]
            ])
        )
    else:
        await query.edit_message_text("Offer not found")

async def grant_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Grant admin rights to a user"""
    user_id = update.effective_user.id
    if not await is_admin(user_id):
        await update.message.reply_text("🚫 You don't have permission to perform this action.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /grant_admin @username")
        return

    target_username = context.args[0].lstrip('@')
    success = update_user_role(target_username, 'admin')

    if not success:
        await update.message.reply_text("❌ User not found.")
    else:
        await update.message.reply_text(f"✅ User @{target_username} has been granted admin rights.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the conversation and clear user data"""
    await update.message.reply_text("❌ Offer creation cancelled.")
    context.user_data.clear()
    return ConversationHandler.END 
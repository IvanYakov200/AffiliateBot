from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config.config import *
from database.database import get_user_role, get_offer_details, add_offer_to_db, update_offer_field, get_all_offers, get_db_connection
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
    event_name = update.message.text
    print(f"Debug: Saving event_name: {event_name}")
    context.user_data['event_name'] = event_name
    print(f"Debug: context.user_data after saving: {context.user_data}")
    await update.message.reply_text("Enter daily traffic limit:")
    return OFFER_DAILY_LIMIT

async def process_offer_daily_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        daily_limit = int(update.message.text)
        if daily_limit <= 0:
            await update.message.reply_text("Please enter a positive number for daily limit. Try again:")
            return OFFER_DAILY_LIMIT
            
        # Сохраняем daily_limit
        context.user_data['daily_limit'] = daily_limit
        
        # Проверяем наличие event_name
        if 'event_name' not in context.user_data:
            await update.message.reply_text("Error: Event name was not saved. Please start over.")
            return ConversationHandler.END
            
        print(f"Debug: Creating offer with data: {context.user_data}")
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
            'event_name': context.user_data['event_name'],  # Используем сохраненное значение
            'daily_limit': context.user_data['daily_limit']
        }
        print(f"Debug: Final offer_data: {offer_data}")
        add_offer_to_db(offer_data)
        await update.message.reply_text("✅ Offer successfully added!")
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Please enter a valid number for daily limit. Try again:")
        return OFFER_DAILY_LIMIT

async def list_offers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    role = get_user_role(user_id)
    offers = get_all_offers()
    
    print(f"Debug: Retrieved {len(offers) if offers else 0} offers")
    if offers:
        print(f"Debug: First offer: {offers[0]}")

    if not offers:
        if update.callback_query:
            await update.callback_query.edit_message_text("No active offers.")
        else:
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
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            '📋 Active Offers:',
            reply_markup=reply_markup
        )
    else:
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
        📈 Daily Limit: {offer[12]}
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

async def start_edit_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start editing an offer"""
    # Проверяем, является ли update callback_query или message
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        offer_id = int(query.data.split('_')[2])
    else:
        # Если это текстовое сообщение, используем сохраненный ID
        offer_id = context.user_data.get('editing_offer_id')
        if not offer_id:
            await update.message.reply_text("Error: No offer selected for editing.")
            return ConversationHandler.END
    
    offer = get_offer_details(offer_id)
    
    if not offer:
        if update.callback_query:
            await update.callback_query.edit_message_text("Offer not found")
        else:
            await update.message.reply_text("Offer not found")
        return ConversationHandler.END
    
    context.user_data['editing_offer_id'] = offer_id
    context.user_data['editing_offer'] = offer
    
    keyboard = [
        [InlineKeyboardButton("Name", callback_data="edit_name")],
        [InlineKeyboardButton("Description", callback_data="edit_desc")],
        [InlineKeyboardButton("Payout", callback_data="edit_payout")],
        [InlineKeyboardButton("GEO", callback_data="edit_geo")],
        [InlineKeyboardButton("Vertical", callback_data="edit_vertical")],
        [InlineKeyboardButton("KPI", callback_data="edit_kpi")],
        [InlineKeyboardButton("Tracker", callback_data="edit_tracker")],
        [InlineKeyboardButton("Anti-fraud", callback_data="edit_antifraud")],
        [InlineKeyboardButton("AppsFlyer ID", callback_data="edit_appsflyer")],
        [InlineKeyboardButton("Event Name", callback_data="edit_event")],
        [InlineKeyboardButton("Daily Limit", callback_data="edit_daily_limit")],
        [InlineKeyboardButton("← Back", callback_data="offers_list")]
    ]
    
    text = f"""
    📝 Editing offer: *{offer[1]}*
    
    Select what you want to edit:
    """
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    return EDIT_OFFER_NAME

async def handle_edit_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the choice of what to edit"""
    query = update.callback_query
    await query.answer()
    
    choice = query.data.split('_')[1]
    offer = context.user_data['editing_offer']
    
    edit_prompts = {
        'name': ("Enter new offer name:", EDIT_OFFER_NAME),
        'desc': ("Enter new description:", EDIT_OFFER_DESC),
        'payout': ("Enter new payout amount (USD):", EDIT_OFFER_PAYOUT),
        'geo': ("Enter new target GEO countries (comma-separated):", EDIT_OFFER_GEO),
        'vertical': ("Enter new vertical:", EDIT_OFFER_VERTICAL),
        'kpi': ("Enter new KPI requirements:", EDIT_OFFER_KPI),
        'tracker': ("Enter new tracker:", EDIT_OFFER_TRACKER),
        'antifraud': ("Enter new anti-fraud system:", EDIT_OFFER_ANTIFRAUD),
        'appsflyer': ("Enter new AppsFlyer Offer ID:", EDIT_OFFER_APPSFLYER_ID),
        'event': ("Enter new event name:", EDIT_OFFER_EVENT_NAME),
        'daily_limit': ("Enter new daily traffic limit:", EDIT_OFFER_DAILY_LIMIT)
    }
    
    if choice in edit_prompts:
        prompt, state = edit_prompts[choice]
        await query.edit_message_text(prompt)
        return state
    
    return ConversationHandler.END

async def process_edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process edited offer name"""
    new_name = update.message.text
    offer_id = context.user_data['editing_offer_id']
    update_offer_field(offer_id, 'name', new_name)
    await update.message.reply_text("✅ Offer name updated!")
    return await start_edit_offer(update, context)

async def process_edit_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process edited offer description"""
    new_desc = update.message.text
    offer_id = context.user_data['editing_offer_id']
    update_offer_field(offer_id, 'description', new_desc)
    await update.message.reply_text("✅ Offer description updated!")
    return await start_edit_offer(update, context)

async def process_edit_payout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process edited offer payout"""
    try:
        new_payout = float(update.message.text)
        offer_id = context.user_data['editing_offer_id']
        update_offer_field(offer_id, 'payout', new_payout)
        await update.message.reply_text("✅ Offer payout updated!")
        return await start_edit_offer(update, context)
    except ValueError:
        await update.message.reply_text("Please enter a valid number for payout. Try again:")
        return EDIT_OFFER_PAYOUT

async def process_edit_geo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process edited offer GEO"""
    new_geo = update.message.text
    offer_id = context.user_data['editing_offer_id']
    update_offer_field(offer_id, 'geo', new_geo)
    await update.message.reply_text("✅ Offer GEO updated!")
    return await start_edit_offer(update, context)

async def process_edit_vertical(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process edited offer vertical"""
    new_vertical = update.message.text
    offer_id = context.user_data['editing_offer_id']
    update_offer_field(offer_id, 'vertical', new_vertical)
    await update.message.reply_text("✅ Offer vertical updated!")
    return await start_edit_offer(update, context)

async def process_edit_kpi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process edited offer KPI"""
    new_kpi = update.message.text
    offer_id = context.user_data['editing_offer_id']
    update_offer_field(offer_id, 'kpi', new_kpi)
    await update.message.reply_text("✅ Offer KPI updated!")
    return await start_edit_offer(update, context)

async def process_edit_tracker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process edited offer tracker"""
    new_tracker = update.message.text
    offer_id = context.user_data['editing_offer_id']
    update_offer_field(offer_id, 'tracker', new_tracker)
    await update.message.reply_text("✅ Offer tracker updated!")
    return await start_edit_offer(update, context)

async def process_edit_antifraud(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process edited offer anti-fraud"""
    new_antifraud = update.message.text
    offer_id = context.user_data['editing_offer_id']
    update_offer_field(offer_id, 'antifraud', new_antifraud)
    await update.message.reply_text("✅ Offer anti-fraud updated!")
    return await start_edit_offer(update, context)

async def process_edit_appsflyer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process edited offer AppsFlyer ID"""
    new_appsflyer = update.message.text
    offer_id = context.user_data['editing_offer_id']
    update_offer_field(offer_id, 'appsflyer_offer_id', new_appsflyer)
    await update.message.reply_text("✅ Offer AppsFlyer ID updated!")
    return await start_edit_offer(update, context)

async def process_edit_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process edited offer event name"""
    new_event = update.message.text
    offer_id = context.user_data['editing_offer_id']
    update_offer_field(offer_id, 'event_name', new_event)
    await update.message.reply_text("✅ Offer event name updated!")
    return await start_edit_offer(update, context)

async def process_edit_daily_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process edited offer daily limit"""
    try:
        new_limit = int(update.message.text)
        if new_limit <= 0:
            await update.message.reply_text("Please enter a positive number for daily limit. Try again:")
            return EDIT_OFFER_DAILY_LIMIT
        offer_id = context.user_data['editing_offer_id']
        update_offer_field(offer_id, 'daily_limit', new_limit)
        await update.message.reply_text("✅ Offer daily limit updated!")
        return await start_edit_offer(update, context)
    except ValueError:
        await update.message.reply_text("Please enter a valid number for daily limit. Try again:")
        return EDIT_OFFER_DAILY_LIMIT

async def delete_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle offer deletion"""
    query = update.callback_query
    await query.answer()
    
    offer_id = int(query.data.split('_')[2])
    offer = get_offer_details(offer_id)
    
    if not offer:
        await query.edit_message_text("Offer not found")
        return
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, delete", callback_data=f"confirm_delete_{offer_id}"),
            InlineKeyboardButton("❌ No, cancel", callback_data=f"offer_view_{offer_id}")
        ]
    ]
    
    await query.edit_message_text(
        f"Are you sure you want to delete offer *{offer[1]}*?",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def confirm_delete_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and execute offer deletion"""
    query = update.callback_query
    await query.answer()
    
    offer_id = int(query.data.split('_')[2])
    offer = get_offer_details(offer_id)
    
    if not offer:
        await query.edit_message_text("Offer not found")
        return
    
    try:
        # Delete offer from database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM offers WHERE id = ?", (offer_id,))
        conn.commit()
        conn.close()
        
        await query.edit_message_text(
            f"✅ Offer has been deleted successfully.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("← Back to offers", callback_data="offers_list")]
            ])
        )
    except Exception as e:
        await query.edit_message_text(
            f"❌ Error deleting offer: {str(e)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("← Back to offers", callback_data="offers_list")]
            ])
        )

async def handle_offer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle offer management callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "offers_list":
        # Return to offers list
        await list_offers(update, context)
    elif query.data.startswith("offer_view_"):
        # Show offer details
        await show_offer_details(update, context)
    elif query.data.startswith("offer_edit_"):
        # Start editing offer
        return await start_edit_offer(update, context)
    elif query.data.startswith("edit_"):
        # Handle edit choice
        return await handle_edit_choice(update, context)
    elif query.data.startswith("offer_delete_"):
        # Handle delete action
        await delete_offer(update, context)
    elif query.data.startswith("confirm_delete_"):
        # Handle delete confirmation
        await confirm_delete_offer(update, context)

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
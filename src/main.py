from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ConversationHandler,
    ContextTypes
)

from config.config import (
    TELEGRAM_TOKEN, logger,
    OFFER_NAME, OFFER_DESC, OFFER_PAYOUT, OFFER_GEO,
    OFFER_VERTICAL, OFFER_KPI, OFFER_TRACKER, OFFER_ANTIFRAUD,
    OFFER_APPSFLYER_ID, OFFER_EVENT_NAME,
    REPORT_TYPE_SELECT, REPORT_DATES, REPORT_EVENT_NAME,
    REPORT_FIELDS_SELECT, REPORT_CUSTOM_FIELDS, REPORT_SELECT_OFFER,
    REPORT_EVENT_INPUT, REPORT_POST_ATTRIBUTION,
    ANALYSIS_TYPE, ANALYSIS_OFFER_SELECT, ANALYSIS_DATES,
    ANALYSIS_SOURCE_CHOICE, ANALYSIS_MEDIA_SOURCE, ANALYSIS_PARAMS
)
from database.database import init_database
from handlers.offer_handlers import (
    start_add_offer, process_offer_name, process_offer_desc,
    process_offer_payout, process_offer_geo, process_offer_vertical,
    process_offer_kpi, process_offer_tracker, process_offer_antifraud,
    process_appsflyer_id, process_offer_event_name, list_offers,
    show_offer_details, cancel
)
from handlers.report_handlers import (
    start_report, select_report_type, handle_event_choice,
    process_event_name, handle_fields_choice, process_custom_fields,
    process_dates, select_offer
)
from handlers.analysis_handlers import (
    start_analysis, process_analysis_type, select_analysis_offer,
    process_analysis_dates, handle_source_choice, process_media_source,
    handle_media_source_confirmation, perform_analysis
)

async def start(update, context):
    """Start command handler"""
    await update.message.reply_text(
        f"👋 Hello {update.effective_user.first_name}! I'm your Affiliate Marketing Assistant.\n"
        "I can help you manage partner campaigns, offers and analyze performance.\n\n"
        "🔍 Type /help to see all available commands and their descriptions."
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel and end the conversation."""
    await update.message.reply_text("❌ Operation cancelled.")
    return ConversationHandler.END

async def help_command(update, context):
    help_text = """
    📚 Available Commands:
    /start - Start working with bot
    /help - Help information
    /offers - List of offers
    /report - Generate report with offer selection
      Types: installs, events, post-attribution
      Date format: YYYY-MM-DD
    /analyze - Analytics and forecasting
    /cancel - Cancel current operation

    👨💻 Admin Commands:
    /addoffer - Add new offer
    /grant_admin @user - Grant admin rights
    """
    await update.message.reply_text(help_text)

async def handle_message(update, context):
    await update.message.reply_text(
        "❌ Text commands are not supported.\n"
        "Please use the command menu or type /help to see all available commands."
    )

def main():
    """Start the bot."""
    # Initialize database
    init_database()

    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add offer conversation handler
    add_offer_conv = ConversationHandler(
        entry_points=[CommandHandler('addoffer', start_add_offer)],
        states={
            OFFER_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_offer_name),
                CommandHandler('cancel', cancel)
            ],
            OFFER_DESC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_offer_desc),
                CommandHandler('cancel', cancel)
            ],
            OFFER_PAYOUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_offer_payout),
                CommandHandler('cancel', cancel)
            ],
            OFFER_GEO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_offer_geo),
                CommandHandler('cancel', cancel)
            ],
            OFFER_VERTICAL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_offer_vertical),
                CommandHandler('cancel', cancel)
            ],
            OFFER_KPI: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_offer_kpi),
                CommandHandler('cancel', cancel)
            ],
            OFFER_TRACKER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_offer_tracker),
                CommandHandler('cancel', cancel)
            ],
            OFFER_ANTIFRAUD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_offer_antifraud),
                CommandHandler('cancel', cancel)
            ],
            OFFER_APPSFLYER_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_appsflyer_id),
                CommandHandler('cancel', cancel)
            ],
            OFFER_EVENT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_offer_event_name),
                CommandHandler('cancel', cancel)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        name="add_offer_conversation",
        persistent=False
    )

    # Add report conversation handler
    report_conv = ConversationHandler(
        entry_points=[CommandHandler('report', start_report)],
        states={
            REPORT_TYPE_SELECT: [
                CallbackQueryHandler(select_report_type),
                CommandHandler('cancel', cancel)
            ],
            REPORT_EVENT_INPUT: [
                CallbackQueryHandler(handle_event_choice),
                CommandHandler('cancel', cancel)
            ],
            REPORT_EVENT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_event_name),
                CommandHandler('cancel', cancel)
            ],
            REPORT_FIELDS_SELECT: [
                CallbackQueryHandler(handle_fields_choice),
                CommandHandler('cancel', cancel)
            ],
            REPORT_CUSTOM_FIELDS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_custom_fields),
                CommandHandler('cancel', cancel)
            ],
            REPORT_DATES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_dates),
                CommandHandler('cancel', cancel)
            ],
            REPORT_SELECT_OFFER: [
                CallbackQueryHandler(select_offer),
                CommandHandler('cancel', cancel)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        name="report_conversation",
        persistent=False
    )

    # Add analysis conversation handler
    analysis_conv = ConversationHandler(
        entry_points=[CommandHandler('analyze', start_analysis)],
        states={
            ANALYSIS_TYPE: [
                CallbackQueryHandler(process_analysis_type),
                CommandHandler('cancel', cancel)
            ],
            ANALYSIS_OFFER_SELECT: [
                CallbackQueryHandler(select_analysis_offer),
                CommandHandler('cancel', cancel)
            ],
            ANALYSIS_DATES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_analysis_dates),
                CommandHandler('cancel', cancel)
            ],
            ANALYSIS_SOURCE_CHOICE: [
                CallbackQueryHandler(handle_source_choice),
                CommandHandler('cancel', cancel)
            ],
            ANALYSIS_MEDIA_SOURCE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_media_source),
                CommandHandler('cancel', cancel)
            ],
            ANALYSIS_PARAMS: [
                CallbackQueryHandler(handle_media_source_confirmation),
                CommandHandler('cancel', cancel)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        name="analysis_conversation",
        persistent=False
    )

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("offers", list_offers))
    application.add_handler(add_offer_conv)
    application.add_handler(report_conv)
    application.add_handler(analysis_conv)
    application.add_handler(CallbackQueryHandler(show_offer_details, pattern=r"^offer_view_\d+$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Setup commands
    commands = [
        BotCommand("start", "Start working with bot"),
        BotCommand("help", "Help information"),
        BotCommand("offers", "List of offers"),
        BotCommand("addoffer", "Add new offer (Admin only)"),
        BotCommand("report", "Generate report with offer selection"),
        BotCommand("analyze", "Analytics and forecasting"),
        BotCommand("grant_admin", "Grant admin rights (Admin only)"),
        BotCommand("cancel", "Cancel current operation")
    ]
    
    async def post_init(app: Application) -> None:
        """Post initialization hook to set up commands."""
        await app.bot.set_my_commands(commands)

    application.post_init = post_init

    # Start the bot
    print("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nBot stopped gracefully!")
    except Exception as e:
        print(f"Error occurred: {e}")
        raise 
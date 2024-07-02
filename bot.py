from src.config.settings import BOT_TOKEN
from src.handlers.command_handlers import start, view_history, show_today_transactions
from src.handlers.query_handlers import handle_exchange_selection, handle_admin_response
from src.handlers.message_handlers import handle_amount_entry, user_contact, user_photo
from src.services.rate_service import fetch_cbu_rates, update_cbu_rates, update_exchange_rates
from src.utils.logging import setup_logging
from src.models.db import create_tables
from src.utils.utility_functions import update_dynamic_spreads
from web_server import run_web_server

import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit
import threading

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.start()

    scheduler.add_job(
        func=update_dynamic_spreads,
        trigger=IntervalTrigger(minutes=360),  # Adjust spreads every 6 hours
        id='update_dynamic_spreads',
        name='Update dynamic spreads every 6 hours',
        replace_existing=True
    )

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

def main():
    # Create tables in the database
    create_tables()

    # Fetch and update exchange rates
    cbu_rates = fetch_cbu_rates()
    update_cbu_rates(cbu_rates)
    update_exchange_rates()

    # Start the scheduler for dynamic spreads
    start_scheduler()

    # Start the web server in a separate thread
    threading.Thread(target=run_web_server, daemon=True).start()
    
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("history", view_history))
    application.add_handler(MessageHandler(filters.CONTACT, user_contact))
    application.add_handler(MessageHandler(filters.PHOTO, user_photo))
    application.add_handler(CallbackQueryHandler(handle_exchange_selection))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount_entry))
    application.add_handler(CommandHandler("today_transactions", show_today_transactions))
    application.add_handler(CallbackQueryHandler(handle_admin_response, pattern='^(approve|deny)_'))
    application.run_polling()

if __name__ == '__main__':
    main()

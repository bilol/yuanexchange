import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CallbackContext
from src.models.user_model import user_exists, get_user_status, get_user_language
from src.models.transaction_model import fetch_user_transactions, fetch_user_transactions_for_today
from src.utils.buttons import main_menu_buttons
from src.utils.translations import translate
from src.utils.logging import setup_logging

logger = setup_logging()

async def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = user.id
    first_name = user.first_name
    user_lang = 'en'

    if not user_exists(user_id):
        await send_contact_request(update, user_lang, first_name)
    else:
        await handle_existing_user(update, user_id, first_name)

async def send_contact_request(update: Update, user_lang: str, first_name: str):
    contact_button = KeyboardButton(text=translate('share_contact', user_lang), request_contact=True)
    reply_markup = ReplyKeyboardMarkup([[contact_button]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        translate('start_message', user_lang).format(name=first_name),
        reply_markup=reply_markup
    )

async def handle_existing_user(update: Update, user_id: int, first_name: str):
    user_status = get_user_status(user_id)
    user_lang = get_user_language(user_id)
    if user_status == 'approved':
        await update.message.reply_text(
            translate('welcome_back_message', user_lang).format(name=first_name),
            reply_markup=main_menu_buttons(user_lang)
        )
    else:
        await update.message.reply_text(
            translate('info_under_review', user_lang),
            reply_markup=ReplyKeyboardRemove()
        )

async def view_history(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
    user_lang = get_user_language(user_id)
    transactions = fetch_user_transactions(user_id)
    
    if not transactions:
        await send_no_transactions_message(update, user_lang)
    else:
        await send_transactions_history(update, user_lang, transactions)

async def send_no_transactions_message(update: Update, user_lang: str):
    message = translate('no_transactions', user_lang)
    if update.message:
        await update.message.reply_text(message)
    else:
        await update.callback_query.message.reply_text(message)

async def send_transactions_history(update: Update, user_lang: str, transactions: list):
    history_message = translate('transaction_history', user_lang)
    history_message += format_transactions(transactions, user_lang)
    
    if update.message:
        await update.message.reply_text(history_message)
    else:
        await update.callback_query.message.reply_text(history_message)

def format_transactions(transactions: list, user_lang: str) -> str:
    formatted_transactions = ""
    for txn in transactions:
        timestamp, exchange_type, amount, rate, received_amount = txn
        date_str = timestamp.strftime("%d-%m-%Y")
        time_str = timestamp.strftime("%H:%M:%S")
        currency_from, currency_to = exchange_type.split('_to_')
        formatted_transactions += (
            f"\n{translate('date_label', user_lang)}: {date_str}\n"
            f"{translate('time_label', user_lang)}: {time_str}\n"
            f"{translate('amount_label', user_lang)}: {amount:,.2f} {currency_from}\n"
            f"{translate('rate_label', user_lang)}: {rate:,.2f}\n"
            f"{translate('received_label', user_lang)}: {received_amount:,.2f} {currency_to}\n"
        )
    return formatted_transactions

async def show_today_transactions(update: Update, context: CallbackContext):
    user_id = update.callback_query.from_user.id
    user_lang = get_user_language(user_id)
    transactions = fetch_user_transactions_for_today()
    
    if not transactions:
        await update.callback_query.message.edit_text(translate('no_transactions_today', user_lang))
    else:
        await send_today_transactions(update, user_lang, transactions)

async def send_today_transactions(update: Update, user_lang: str, transactions: list):
    transactions_message = translate('today_transactions', user_lang)
    transactions_message += format_today_transactions(transactions, user_lang)
    await update.callback_query.message.edit_text(transactions_message)

def format_today_transactions(transactions: list, user_lang: str) -> str:
    formatted_transactions = ""
    for i, txn in enumerate(transactions, start=1):
        timestamp, exchange_type, amount, rate, received_amount, username, phone_number = txn
        date_str = timestamp.strftime("%Y-%m-%d")
        time_str = timestamp.strftime("%H:%M:%S")
        currency_from, currency_to = exchange_type.split('_to_')
        formatted_transactions += (
            f"\n#{i}\n"
            f"{translate('date_label', user_lang)}: {date_str}\n"
            f"{translate('time_label', user_lang)}: {time_str}\n"
            f"👤 {translate('username', user_lang)}: @{username}\n"
            f"{translate('phone_number', user_lang)}: {phone_number}\n"
            f"{translate('amount_label', user_lang)}: {amount:,.2f} {currency_from}\n"
            f"{translate('rate_label', user_lang)}: {rate:,.2f}\n"
            f"{translate('received_label', user_lang)}: {received_amount:,.2f} {currency_to}\n"
        )
    return formatted_transactions

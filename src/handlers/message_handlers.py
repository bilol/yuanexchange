import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from decimal import Decimal, InvalidOperation
from datetime import datetime

from src.config.settings import ADMIN_USER_ID  # Import ADMIN_USER_ID
from src.models.user_model import get_user_language, user_exists, add_user, update_user_status
from src.models.transaction_model import log_transaction
from src.utils.translations import translate
from src.utils.logging import setup_logging
from src.utils.utility_functions import fetch_current_rates

logger = setup_logging()

async def handle_amount_entry(update: Update, context: CallbackContext):
    amount_text = update.message.text
    logger.info(f"Received amount text: {amount_text}")

    user_id = update.message.from_user.id
    user_lang = get_user_language(user_id)  # Retrieve the user's language preference

    amount = await parse_amount(amount_text, user_lang, update)
    if amount is None:
        return

    exchange_type = context.user_data.get('exchange_type')
    if not await validate_exchange_type(exchange_type, user_lang, update):
        return

    rates = fetch_current_rates()
    if not rates:
        await update.message.reply_text(translate('error_fetching_rates', user_lang))
        return

    received_amount, rate = await calculate_received_amount(amount, exchange_type, rates, user_lang, update)
    if received_amount is None:
        return

    await log_transaction_details(user_id, update, context, amount, rate, received_amount, exchange_type)

    await send_transaction_confirmation(update, user_lang, amount, rate, received_amount)

async def parse_amount(amount_text: str, user_lang: str, update: Update):
    try:
        amount = Decimal(amount_text)
        logger.info(f"Parsed amount: {amount} (type: {type(amount)})")
        return amount
    except (ValueError, InvalidOperation) as e:
        logger.error(f"Error parsing amount: {e}")
        await update.message.reply_text(translate('invalid_amount', user_lang))
        return None

async def validate_exchange_type(exchange_type: str, user_lang: str, update: Update):
    if not exchange_type or 'to' not in exchange_type:
        await update.message.reply_text(translate('invalid_exchange_type', user_lang))
        return False
    logger.info(f"Exchange type: {exchange_type}")
    return True

async def calculate_received_amount(amount: Decimal, exchange_type: str, rates: dict, user_lang: str, update: Update):
    try:
        rate, received_amount = perform_exchange_calculation(amount, exchange_type, rates)
        logger.info(f"Calculated received amount: {received_amount} at rate: {rate}")
        return received_amount, rate
    except Exception as e:
        logger.error(f"Error during exchange calculation: {e}", exc_info=True)
        await update.message.reply_text(translate('exchange_calculation_error', user_lang))
        return None, None

def perform_exchange_calculation(amount: Decimal, exchange_type: str, rates: dict):
    if exchange_type == 'UZS_to_CNY':
        rate = Decimal(rates['CNY']['sell_rate'])
        received_amount = amount / rate
    elif exchange_type == 'CNY_to_UZS':
        rate = Decimal(rates['CNY']['buy_rate'])
        received_amount = amount * rate
    elif exchange_type == 'USD_to_CNY':
        rate = Decimal(rates['USD']['buy_rate'])
        uzs_amount = amount * rate
        received_amount = uzs_amount / Decimal(rates['CNY']['sell_rate'])
    elif exchange_type == 'CNY_to_USD':
        rate = Decimal(rates['CNY']['buy_rate'])
        uzs_amount = amount * rate
        received_amount = uzs_amount / Decimal(rates['USD']['sell_rate'])
    else:
        raise ValueError('Invalid exchange type')
    return rate, received_amount

async def log_transaction_details(user_id: int, update: Update, context: CallbackContext, amount: Decimal, rate: Decimal, received_amount: Decimal, exchange_type: str):
    user_name = update.message.from_user.username
    user_lang = get_user_language(user_id)
    try:
        log_transaction(user_id, exchange_type, amount, rate, received_amount)
        logger.info(f"Transaction logged: {user_id}, {exchange_type}, {amount}, {rate}, {received_amount}")

        transaction_details = translate('transaction_details', user_lang).format(
            user_name=user_name,
            user_id=user_id,
            amount=float(amount),
            currency_from=exchange_type.split('_to_')[0],
            rate=float(rate),
            received_amount=float(received_amount),
            currency_to=exchange_type.split('_to_')[1]
        )

        logger.info(f"Transaction details: {transaction_details}")
        await context.bot.send_message(chat_id=ADMIN_USER_ID, text=transaction_details)
    except Exception as e:
        logger.error(f"Error logging transaction: {e}", exc_info=True)
        await update.message.reply_text(translate('transaction_error', user_lang))

async def send_transaction_confirmation(update: Update, user_lang: str, amount: Decimal, rate: Decimal, received_amount: Decimal):
    await update.message.reply_text(
        text=translate('transaction_confirmation', user_lang).format(
            received_amount=float(received_amount),
            amount=float(amount),
            rate=float(rate)
        )
    )

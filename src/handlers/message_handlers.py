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
from src.utils.buttons import main_menu_buttons
from src.utils.utility_functions import fetch_current_rates

logger = setup_logging()

async def handle_amount_entry(update: Update, context: CallbackContext):
    amount_text = update.message.text
    logger.info(f"Received amount text: {amount_text}")

    user_id = update.message.from_user.id
    user_lang = get_user_language(user_id)  # Retrieve the user's language preference

    try:
        amount = Decimal(amount_text)
        context.user_data['amount'] = amount
        logger.info(f"Parsed amount: {amount} (type: {type(amount)})")
    except (ValueError, InvalidOperation) as e:
        logger.error(f"Error parsing amount: {e}")
        await update.message.reply_text(translate('invalid_amount', user_lang))
        return

    exchange_type = context.user_data.get('exchange_type')
    if not exchange_type or 'to' not in exchange_type:
        await update.message.reply_text(translate('invalid_exchange_type', user_lang))
        return

    currency_from, currency_to = exchange_type.split('_to_')
    logger.info(f"Exchange type: {exchange_type}, from: {currency_from}, to: {currency_to}")

    rates = fetch_current_rates()
    if not rates:
        await update.message.reply_text(translate('error_fetching_rates', user_lang))
        return

    logger.info(f"Fetched rates: {rates}")

    try:
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
            await update.message.reply_text(translate('invalid_exchange_type', user_lang))
            return

        context.user_data['received_amount'] = received_amount
        context.user_data['rate'] = rate

        logger.info(f"Calculated received amount: {received_amount} (type: {type(received_amount)}) at rate: {rate} (type: {type(rate)})")

        user_name = update.message.from_user.username

        # Ensure amount, rate, and received_amount are properly converted to float for formatting
        formatted_amount = float(amount)
        formatted_rate = float(rate)
        formatted_received_amount = float(received_amount)

        logger.info(f"Formatted amount: {formatted_amount} (type: {type(formatted_amount)})")
        logger.info(f"Formatted rate: {formatted_rate} (type: {type(formatted_rate)})")
        logger.info(f"Formatted received amount: {formatted_received_amount} (type: {type(formatted_received_amount)})")

        try:
            log_transaction(user_id, exchange_type, amount, rate, received_amount)
            logger.info(f"Transaction logged: {user_id}, {exchange_type}, {amount}, {rate}, {received_amount}")

            transaction_details = translate('transaction_details', user_lang).format(
                user_name=user_name,
                user_id=user_id,
                amount=formatted_amount,
                currency_from=currency_from,
                rate=formatted_rate,
                received_amount=formatted_received_amount,
                currency_to=currency_to
            )

            logger.info(f"Transaction details: {transaction_details}")
            await context.bot.send_message(chat_id=ADMIN_USER_ID, text=transaction_details)
        except Exception as e:
            logger.error(f"Error logging transaction: {e}", exc_info=True)
            await update.message.reply_text(translate('transaction_error', user_lang))
            return

        # Update the transaction confirmation message as well
        await update.message.reply_text(
            text=translate('transaction_confirmation', user_lang).format(
                received_amount=formatted_received_amount,
                amount=formatted_amount,
                rate=formatted_rate
            )
        )

    except Exception as e:
        logger.error(f"Error during exchange calculation: {e}", exc_info=True)
        await update.message.reply_text(translate('exchange_calculation_error', user_lang))


async def user_contact(update: Update, context: CallbackContext):
    contact = update.message.contact
    user_id = contact.user_id
    first_name = contact.first_name
    last_name = contact.last_name
    phone_number = contact.phone_number

    username = update.message.from_user.username
    user_lang = 'en'

    if not user_exists(user_id):
        add_user(user_id, first_name, last_name, username, phone_number, user_lang, datetime.now(), user_status='pending')
        await update.message.reply_text(
            translate('send_passport_photo', user_lang),
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        user_lang = get_user_language(user_id)
        await update.message.reply_text(
            translate('already_registered', user_lang),
            reply_markup=main_menu_buttons(user_lang)
        )


async def user_photo(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_lang = get_user_language(user_id)

    user = update.message.from_user
    username = user.username
    first_name = user.first_name
    phone_number = None

    # Retrieve the phone number from the contact if available
    if update.message.contact:
        phone_number = update.message.contact.phone_number

    photo = update.message.photo[-1]
    file = await photo.get_file()

    try:
        await context.bot.send_photo(
            chat_id=ADMIN_USER_ID,
            photo=photo.file_id,
            caption=f"User ID: {user_id}\nUsername: @{username}\nFirst Name: {first_name}\nPhone Number: {phone_number}\nReview the passport photo.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Approve", callback_data=f'approve_{user_id}'), 
                 InlineKeyboardButton("Deny", callback_data=f'deny_{user_id}')]
            ])
        )
        logger.info(f"Sent passport photo of user {user_id} to admin with username, first name, and phone number")
    except Exception as e:
        logger.error(f"Error sending photo to admin: {e}", exc_info=True)

    update_user_status(user_id, 'pending')

    await update.message.reply_text(
        translate('info_under_review', user_lang),
        reply_markup=ReplyKeyboardRemove()
    )
    logger.info(f"Set user {user_id} status to 'pending'")
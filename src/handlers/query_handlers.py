import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from src.models.user_model import get_user_language, update_user_language, update_user_status,get_user_info
from src.models.transaction_model import fetch_user_transactions_for_today, update_transaction_status
from src.utils.buttons import main_menu_buttons, language_buttons, exchange_type_buttons
from src.utils.translations import translate
from src.utils.logging import setup_logging
from src.utils.utility_functions import fetch_current_rates
from src.handlers.command_handlers import view_history  # Import view_history

logger = setup_logging()

async def handle_exchange_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_lang = get_user_language(query.from_user.id)

    if query.data.startswith('approve_') or query.data.startswith('deny_'):
        await handle_admin_response(update, context)
        return

    if query.data == 'show_rates':
        rates = fetch_current_rates()
        if not rates:
            await query.edit_message_text(text=translate('error_fetching_rates', user_lang))
            return

        rates_message = translate('current_rates', user_lang)
        for currency, rate in rates.items():
            if currency in ['USD', 'CNY']:
                rates_message += (
                    f"{currency}:\n"
                    f"  💵 BUY: {rate['buy_rate']:,.2f}\n"
                    f"  💰 SELL: {rate['sell_rate']:,.2f}\n"
                )
        await query.edit_message_text(text=rates_message)
        return

    if query.data == 'history':
        await view_history(update, context)
        return

    if query.data == 'exchange':
        await query.message.reply_text(
            text=translate('exchange_prompt', user_lang),
            reply_markup=exchange_type_buttons(user_lang)
        )
        return

    if query.data == 'set_language':
        await query.message.reply_text(
            text=translate('choose_language', user_lang),
            reply_markup=language_buttons(user_lang)
        )
        return

    if query.data == 'show_today_transactions':
        await show_today_transactions(update, context)
        return

    if query.data.startswith('setlang_'):
        lang = query.data.split('_')[1]
        user_id = query.from_user.id
        update_user_language(user_id, lang)
        await query.edit_message_text(translate('language_set', lang).format(language=lang))
        return

    exchange_type = query.data
    context.user_data['exchange_type'] = exchange_type

    await query.message.reply_text(
        text=translate('exchange_amount_prompt', user_lang).format(exchange_type=exchange_type)
    )


async def handle_admin_response(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split('_')[1])
    action = query.data.split('_')[0]
    user_lang = get_user_language(user_id)

    # Retrieve user information
    user_info = get_user_info(user_id)
    if not user_info:
        await query.edit_message_text("User information not found.")
        return

    username, first_name, phone_number = user_info

    if action == 'approve':
        update_user_status(user_id, 'approved')
        await context.bot.send_message(
            chat_id=user_id,
            text=translate('approved_message', user_lang),
            reply_markup=main_menu_buttons(user_lang)
        )
        await query.edit_message_caption(
            caption=f"User ID: {user_id}\nUsername: @{username}\nFirst Name: {first_name}\nPhone Number: {phone_number}\n",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Approved", callback_data='approved')]
            ])
        )
    elif action == 'deny':
        update_user_status(user_id, 'denied')
        await context.bot.send_message(
            chat_id=user_id,
            text=translate('denied_message', user_lang)
        )
        await query.edit_message_caption(
            caption=f"User ID: {user_id}\nUsername: @{username}\nFirst Name: {first_name}\nPhone Number: {phone_number}\n",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Denied", callback_data='denied')]
            ])
        )


async def show_today_transactions(update: Update, context: CallbackContext):
    user_id = update.callback_query.from_user.id
    user_lang = get_user_language(user_id)

    transactions = fetch_user_transactions_for_today()
    if not transactions:
        await update.callback_query.message.edit_text(translate('no_transactions_today', user_lang))
        return

    transactions_message = translate('today_transactions', user_lang)
    for i, txn in enumerate(transactions, start=1):
        timestamp, exchange_type, amount, rate, received_amount, username, phone_number = txn
        date_str = timestamp.strftime("%Y-%m-%d")
        time_str = timestamp.strftime("%H:%M:%S")
        currency_from, currency_to = exchange_type.split('_to_')
        transactions_message += (
            f"\n#{i}\n"
            f"{translate('date_label', user_lang)}: {date_str}\n"
            f"{translate('time_label', user_lang)}: {time_str}\n"
            f"👤 {translate('username', user_lang)}: @{username}\n"
            f"{translate('phone_number', user_lang)}: {phone_number}\n"
            f"{translate('amount_label', user_lang)}: {amount:,.2f} {currency_from}\n"
            f"{translate('rate_label', user_lang)}: {rate:,.2f}\n"
            f"{translate('received_label', user_lang)}: {received_amount:,.2f} {currency_to}\n"
        )

    await update.callback_query.message.edit_text(transactions_message)

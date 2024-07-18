import logging
from telegram import Update, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from datetime import datetime

from src.config.settings import ADMIN_USER_ID  # Import ADMIN_USER_ID
from src.models.user_model import get_user_language, user_exists, add_user, update_user_status, get_user_info
from src.utils.translations import translate
from src.utils.logging import setup_logging
from src.utils.buttons import main_menu_buttons

logger = setup_logging()

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
    phone_number = update.message.contact.phone_number if update.message.contact else None

    photo = update.message.photo[-1]

    await send_photo_to_admin(context, user_id, username, first_name, phone_number, photo)
    update_user_status(user_id, 'pending')

    await update.message.reply_text(
        translate('info_under_review', user_lang),
        reply_markup=ReplyKeyboardRemove()
    )
    logger.info(f"Set user {user_id} status to 'pending'")

async def send_photo_to_admin(context: CallbackContext, user_id: int, username: str, first_name: str, phone_number: str, photo):
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

async def handle_admin_response(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split('_')[1])
    action = query.data.split('_')[0]
    user_lang = get_user_language(user_id)

    user_info = get_user_info(user_id)
    if not user_info:
        await query.edit_message_text("User information not found.")
        return

    username, first_name, phone_number = user_info
    if action == 'approve':
        await approve_user(query, context, user_id, user_lang, username, first_name, phone_number)
    elif action == 'deny':
        await deny_user(query, context, user_id, user_lang, username, first_name, phone_number)

async def approve_user(query, context, user_id, user_lang, username, first_name, phone_number):
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

async def deny_user(query, context, user_id, user_lang, username, first_name, phone_number):
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

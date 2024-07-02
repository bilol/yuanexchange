from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from .translations import translate

def main_menu_buttons(user_lang):
    keyboard = [
        [InlineKeyboardButton(translate('exchange_button', user_lang), callback_data='exchange')],
        [InlineKeyboardButton(translate('history_button', user_lang), callback_data='history')],
        [InlineKeyboardButton(translate('show_rates_button', user_lang), callback_data='show_rates')],
        [InlineKeyboardButton(translate('set_language_button', user_lang), callback_data='set_language')],
        [InlineKeyboardButton(translate('today_transactions_button', user_lang), callback_data='show_today_transactions')]
    ]
    return InlineKeyboardMarkup(keyboard)

def language_buttons(user_lang):
    keyboard = [
        [InlineKeyboardButton("English", callback_data='setlang_en')],
        [InlineKeyboardButton("O'zbek", callback_data='setlang_uz')],
        [InlineKeyboardButton("Русский", callback_data='setlang_ru')]
    ]
    return InlineKeyboardMarkup(keyboard)

def exchange_type_buttons(user_lang):
    keyboard = [
        [
            InlineKeyboardButton(translate('UZS_to_CNY_button', user_lang), callback_data='UZS_to_CNY'),
            InlineKeyboardButton(translate('CNY_to_UZS_button', user_lang), callback_data='CNY_to_UZS')
        ],
        [
            InlineKeyboardButton(translate('USD_to_CNY_button', user_lang), callback_data='USD_to_CNY'),
            InlineKeyboardButton(translate('CNY_to_USD_button', user_lang), callback_data='CNY_to_USD')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

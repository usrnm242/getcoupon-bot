import telebot
import re
import Levenshtein as levenshtein
from fuzzywuzzy import fuzz
from collections import defaultdict

from get_db import get_db


TOKEN = "1315357078:AAE9GQNe2cPVkqu2rOx5rPKnNlpUhOUaUNg"

bot = telebot.TeleBot(TOKEN)

user_current_coupon_index = defaultdict(int)


database = get_db()

all_shop_names = database.keys()
all_shop_names_lower = list(map(lambda s: s.lower(), all_shop_names))


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(message.from_user.id, "Просто пришли мне имя магазина, а в ответ я пришлю тебе все купоны и промокоды, которые у меня есть")
    bot.send_message(message.from_user.id, "Кстати, у нас есть приложение в App Store)) скачивай! Там тоже удобный поиск)\nhttps://apps.apple.com/ru/app/getcoupon-купоны-и-акции/id1525623085", disable_web_page_preview=True)


@bot.message_handler(content_types=['text'])
def get(message):
    coupons, keyboard = get_coupon(message.text)
    global user_current_coupon_index
    user_current_coupon_index[message.from_user.id] = 0

    bot.send_message(message.from_user.id,
                     coupons[user_current_coupon_index[message.from_user.id]],
                     reply_markup=keyboard,
                     disable_web_page_preview=True)


@bot.callback_query_handler(func=lambda f: True)
def inline(callback):
    user_id = callback.message.chat.id
    shop = callback.data[1:]

    if callback.data.startswith("<"):
        user_current_coupon_index[user_id] -= 1
    else:
        # "right;"
        user_current_coupon_index[user_id] += 1

    new_text = get_coupon_by_index(shop, user_current_coupon_index[user_id])

    bot.edit_message_text(chat_id=user_id,
                          message_id=callback.message.message_id,
                          text=new_text,
                          reply_markup=_get_markup_keyboard(shop),
                          disable_web_page_preview=True)


def get_coupon(text):
    shop = _search_for_shop(text,
                            all_shop_names,
                            all_shop_names_lower)

    if not shop:
        return [f"Не найден '{text}' в базе данных("], None

    coupons: list = _get_coupons(database, shop)

    if not coupons:
        return [f"Купонов для '{shop}' не найдено("], None

    return coupons, _get_markup_keyboard(shop)


def _get_markup_keyboard(shop: str):
    keyboard = telebot.types.InlineKeyboardMarkup()

    keyboard.row(
        telebot.types.InlineKeyboardButton('<<', callback_data=f"<{shop}"),
        telebot.types.InlineKeyboardButton('>>', callback_data=f">{shop}")
    )

    keyboard.add(
        telebot.types.InlineKeyboardButton(
            f'Перейти на сайт {shop}', url=database[shop]['website_link']
        )
    )

    return keyboard


def _search_for_shop(user_text: str,
                     all_shop_names: list,
                     all_shop_names_lower: list,
                     database: dict = database) -> str:
    """
    Returns:
        str shopname if found
        '' if not found
    """

    partial_ratio_trust_lvl: int = 82

    text = user_text.lower()
    text = re.sub(r"[^a-zа-яё0-9\n \-]", " ", text)
    text = re.sub(r"[ ]+", " ", text)
    text = f" {text} "  # adding spaces for correct partial ratio searching

    for shop, shop_lower in zip(all_shop_names, all_shop_names_lower):
        partial_ratio = fuzz.partial_ratio(text, shop_lower)
        alternative_ratio = fuzz.partial_ratio(text, database[shop]['alternative_name'])
        if partial_ratio > partial_ratio_trust_lvl or \
                alternative_ratio > partial_ratio_trust_lvl:
            return shop

    return ""


def _get_coupons(database, user_shop) -> 'list':
    return database[user_shop]['coupons']


def get_coupon_by_index(shop: str, index: int) -> str:
    all_coupons = database[shop]['coupons']
    all_coupons_len = len(all_coupons)
    return all_coupons[index % all_coupons_len]


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)

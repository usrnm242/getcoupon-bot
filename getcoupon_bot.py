import telebot
import re
from collections import defaultdict
import datetime
import Levenshtein as levenshtein
from fuzzywuzzy import fuzz
from get_db import get_db
from conf import TOKEN


bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()


def update_db():
    db = get_db()
    all_shop_names = db.keys()
    all_shop_names_lower = list(map(lambda s: s.lower(), all_shop_names))
    return db, all_shop_names, all_shop_names_lower


database, all_shop_names, all_shop_names_lower = update_db()
user_current_coupon_index = defaultdict(int)
db_last_update_time = datetime.datetime.now()
db_cache_expiry_interval = datetime.timedelta(minutes=15)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.from_user.id,
        "Просто пришли мне имя магазина, а в ответ я пришлю тебе все купоны "
        "и промокоды, которые у меня есть!"
    )

    bot.send_message(
        message.from_user.id,
        "Кстати, наше приложение `GetCoupon` в "
        "[App Store](https://apps.apple.com/ru/app/getcoupon-купоны-и-акции/id1525623085)"
        " и [Google Play](https://example.com)\n"
        "Скачивай! Там тоже удобный поиск, и всё по полочкам)\n",
        disable_web_page_preview=True,
        parse_mode='Markdown'
    )


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(
        message.from_user.id,
        "Просто пришли мне имя магазина, "
        "а я пришлю список промокодов, которые там действуют."
    )

    bot.send_message(
        message.from_user.id,
        "Не забывай про наше удобное приложение `GetCoupon` для поиска промокодов!",
        reply_markup=_get_markup_keyboard_for_app()
    )


@bot.message_handler(content_types=['text'])
def get(message):
    now = datetime.datetime.now()
    # i know, i have to use cache :(
    global db_last_update_time
    global user_current_coupon_index
    global database
    global all_shop_names
    global all_shop_names_lower

    if now - db_last_update_time >= db_cache_expiry_interval:
        database, all_shop_names, all_shop_names_lower = update_db()
        db_last_update_time = now

    coupons, keyboard = get_coupon(message.text)
    user_current_coupon_index[message.from_user.id] = 0

    bot.send_message(message.from_user.id,
                     coupons[user_current_coupon_index[message.from_user.id]],
                     reply_markup=keyboard,
                     disable_web_page_preview=True,
                     parse_mode='Markdown')


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
                          reply_markup=_get_markup_keyboard_for_shop(shop),
                          disable_web_page_preview=True,
                          parse_mode='Markdown')


def get_coupon(text) -> (list, telebot.types.InlineKeyboardMarkup):
    shop = _search_for_shop(text,
                            all_shop_names,
                            all_shop_names_lower)

    if not shop:
        return [f"Магазин '{text}' не найден в базе данных😔"], None

    coupons: list = _get_coupons(database, shop)

    if not coupons:
        return [f"Купонов для '{shop}' не найдено😔"], _get_markup_keyboard_with_shop_website_link(shop)

    if len(coupons) == 1:
        keyboard = _get_markup_keyboard_with_shop_website_link(shop)
    else:
        keyboard = _get_markup_keyboard_for_shop(shop)

    return coupons, keyboard


def _get_markup_keyboard_for_shop(
        shop: str
        ) -> telebot.types.InlineKeyboardMarkup:

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


def _get_markup_keyboard_with_shop_website_link(
        shop: str
        ) -> telebot.types.InlineKeyboardMarkup:

    keyboard = telebot.types.InlineKeyboardMarkup()

    keyboard.add(
        telebot.types.InlineKeyboardButton(
            f'Перейти на сайт {shop}', url=database[shop]['website_link']
        )
    )

    return keyboard


def _get_markup_keyboard_for_app() -> telebot.types.InlineKeyboardMarkup:
    keyboard = telebot.types.InlineKeyboardMarkup()

    keyboard.row(
        telebot.types.InlineKeyboardButton(
            'App Store',
            url="https://apps.apple.com/ru/app/getcoupon-купоны-и-акции/id1525623085"
        ),
        telebot.types.InlineKeyboardButton(
            'Google Play',
            url="https://example.com"
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
        alternative_ratio = fuzz.partial_ratio(
            text,
            database[shop]['alternative_name']
        )
        if partial_ratio > partial_ratio_trust_lvl or \
                alternative_ratio > partial_ratio_trust_lvl:
            return shop

    return ""


def _get_coupons(database, user_shop) -> 'list':
    return database[user_shop]['coupons']


def get_coupon_by_index(shop: str, index: int) -> str:
    all_coupons = database[shop]['coupons']
    return all_coupons[index % len(all_coupons)]


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=1)

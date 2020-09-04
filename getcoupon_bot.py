import telebot
import re
import Levenshtein as levenshtein
from fuzzywuzzy import fuzz
import json
import db
from conf import TOKEN


bot = telebot.TeleBot(TOKEN)


with open("./utils.json", 'r') as utils_file:
    util_data = json.load(utils_file)

swear_words = util_data["swear_words"]

name_callings = util_data["name_callings"]


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
        "[App Store](https://uadd.me/getcoupon)"
        " и скоро будет в Google Play.\n"
        "Там тоже удобный поиск, и всё по полочкам)\n"
        "Не забывай подписываться на нас в "
        "[соцсетях](https://uadd.me/getcoupon)!\n",
        disable_web_page_preview=True,
        parse_mode='Markdown'
    )


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(
        message.from_user.id,
        "Просто пришли мне название магазина, "
        "а я пришлю список промокодов, которые там действуют."
    )

    bot.send_message(
        message.from_user.id,
        "Смотри наш [сайт-визитку](https://uadd.me/getcoupon) "
        "с другими продуктами!",
        parse_mode='Markdown'
    )


@bot.edited_message_handler(func=lambda message: True)
def edit_message(message):
    bot.edit_message_text(chat_id=message.chat.id,
                          text="Не редачь пажалустааа!",
                          message_id=message.message_id + 1)


@bot.message_handler(content_types=['text'])
def get(message):
    coupons, keyboard = get_coupon(message.text)
    db.set_user_coupon_index(message.from_user.id, 0)
    bot.send_message(message.from_user.id,
                     coupons[db.BotUsers[message.from_user.id].coupon_index],
                     reply_markup=keyboard,
                     disable_web_page_preview=True)


@bot.callback_query_handler(func=lambda f: True)
def inline(callback):
    user_id = callback.message.chat.id
    shop = callback.data[1:]

    if callback.data.startswith("<"):
        db.dec_user_coupon_index(user_id)
    else:
        # callback.data.startswith(">")
        db.inc_user_coupon_index(user_id)

    new_text = get_coupon_by_index(shop, db.BotUsers[user_id].coupon_index)

    bot.edit_message_text(chat_id=user_id,
                          message_id=callback.message.message_id,
                          text=new_text,
                          reply_markup=_get_markup_keyboard_for_shop(shop),
                          disable_web_page_preview=True)


def get_coupon(text) -> (list, telebot.types.InlineKeyboardMarkup):
    text = text.lower()

    shop = _search_for_shop(text)

    if not shop:
        answer_to_curse: tuple = _search_for_swear_words(
            text,
            swear_words,
            name_callings
        )

        if answer_to_curse:
            return answer_to_curse

        return [f"Магазин '{text}' не найден в базе данных😔"], None

    coupons: list = db.get_coupons(shop)

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
            f'Перейти на сайт {shop}', url=db.BotShops[shop].website_link
        )
    )

    return keyboard


def _get_markup_keyboard_with_shop_website_link(
        shop: str
        ) -> telebot.types.InlineKeyboardMarkup:

    keyboard = telebot.types.InlineKeyboardMarkup()

    keyboard.add(
        telebot.types.InlineKeyboardButton(
            f'Перейти на сайт {shop}', url=db.BotShops[shop].website_link
        )
    )

    return keyboard


def _search_for_shop(user_text: str) -> str:
    """
    Returns:
        str shopname if found
        '' if not found
    """

    partial_ratio_trust_lvl: int = 82

    text = re.sub(r"[^a-zа-яё0-9\n \-]", " ", user_text)
    text = re.sub(r"[ ]+", " ", text)
    text = f" {text} "  # adding spaces for correct partial ratio searching

    corresponding_shop = ""
    max_ratio = 0

    for shop in db.get_shops():
        main_partial_ratio = fuzz.partial_ratio(text, f" {shop.shopname_lower} ")

        if shop.alternative_name:
            alternative_partial_ratio = fuzz.partial_ratio(
                text,
                f" {shop.alternative_name} "
            )
        else:
            alternative_partial_ratio = 0

        partial_ratio = max(
            main_partial_ratio,
            alternative_partial_ratio
        )

        if partial_ratio > max(partial_ratio_trust_lvl, max_ratio):
            corresponding_shop = shop.shop
            max_ratio = partial_ratio

    return corresponding_shop


def get_coupon_by_index(shop: str, index: int) -> str:
    all_coupons = list(db.BotShops[shop].coupons)
    return all_coupons[index % len(all_coupons)]


def _search_for_swear_words(
        text: str,
        swear_words: list,
        name_callings: list
        ) -> (list, telebot.types.InlineKeyboardMarkup):

    keyboard = telebot.types.InlineKeyboardMarkup()

    if any(swear_word in text for swear_word in swear_words):
        keyboard.add(
            telebot.types.InlineKeyboardButton(
                'Успокоиться', url="http://listentothe.cloud"
            )
        )
        return ['Я не люблю ругаться... Но сегодня... Тоже не буду. Забыли.'], keyboard

    if any(name_calling in text for name_calling in name_callings):
        keyboard.add(
            telebot.types.InlineKeyboardButton(
                'Мой тебе совет. Жми!', url="https://fucking-great-advice.ru"
            )
        )
        return ['Можешь за меня порадоваться. Ведь я всё равно полезнее тебя.'], keyboard

    return None


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=1)

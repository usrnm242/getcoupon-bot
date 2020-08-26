import telebot
import re
import Levenshtein as levenshtein
from fuzzywuzzy import fuzz
import db
from conf import TOKEN


bot = telebot.TeleBot(TOKEN)


# def update_db():
#     db = get_db()
#     all_shop_names = db.keys()
#     all_shop_names_lower = list(map(lambda s: s.lower(), all_shop_names))
#     return db, all_shop_names, all_shop_names_lower
#
#
# database, all_shop_names, all_shop_names_lower = update_db()
# user_current_coupon_index = defaultdict(int)
# db_last_update_time = datetime.datetime.now()
# db_cache_expiry_interval = datetime.timedelta(minutes=15)


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
        "Не забывай подписываться на нас в [соцсетях](https://uadd.me/getcoupon)!\n",
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


@bot.message_handler(content_types=['text'])
def get(message):
    coupons, keyboard = get_coupon(message.text)
    db.set_user_coupon_index(message.from_user.id, 0)
    bot.send_message(message.from_user.id,
                     coupons[db.BotUsers[message.from_user.id].coupon_index],
                     reply_markup=keyboard,
                     disable_web_page_preview=True,
                     parse_mode='Markdown')


@bot.callback_query_handler(func=lambda f: True)
def inline(callback):
    user_id = callback.message.chat.id
    shop = callback.data[1:]

    if callback.data.startswith("<"):
        db.dec_user_coupon_index(user_id)
    else:
        # "right;"
        db.inc_user_coupon_index(user_id)

    new_text = get_coupon_by_index(shop, db.BotUsers[user_id].coupon_index)

    bot.edit_message_text(chat_id=user_id,
                          message_id=callback.message.message_id,
                          text=new_text,
                          reply_markup=_get_markup_keyboard_for_shop(shop),
                          disable_web_page_preview=True,
                          parse_mode='Markdown')


def get_coupon(text) -> (list, telebot.types.InlineKeyboardMarkup):
    shop = _search_for_shop(text)

    if not shop:
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


def _search_for_shop(user_text: str) -> str:
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

    for shop in db.get_shops():
        partial_ratio = fuzz.partial_ratio(text, shop.shopname_lower)
        alternative_ratio = fuzz.partial_ratio(
            text,
            shop.alternative_name
        )
        if partial_ratio > partial_ratio_trust_lvl or \
                alternative_ratio > partial_ratio_trust_lvl:
            return shop.shop

    return ""


def get_coupon_by_index(shop: str, index: int) -> str:
    all_coupons = list(db.BotShops[shop].coupons)
    return all_coupons[index % len(all_coupons)]


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=1)

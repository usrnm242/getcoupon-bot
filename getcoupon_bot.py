import telebot
import re
import json
import Levenshtein as levenshtein
from fuzzywuzzy import fuzz


TOKEN = "1315357078:AAE9GQNe2cPVkqu2rOx5rPKnNlpUhOUaUNg"

bot = telebot.TeleBot(TOKEN)


def convert_database(db_file: str):
    with open(db_file, 'r') as f:
        original_db = json.loads(f.read())

    database = []
    all_shop_names = []
    all_shop_names_lower = []

    for category in original_db:
        database.extend(category['shops'])
        for shop in category['shops']:
            all_shop_names.append(shop['name'])
            all_shop_names_lower.append(shop['name'].lower())

    return database, all_shop_names, all_shop_names_lower


database, all_shop_names, all_shop_names_lower = \
    convert_database('./ios-collections.json')


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(message.from_user.id, "Просто пришли мне имя магазина, а в ответ я пришлю тебе все купоны и промокоды, которые у меня есть")
    bot.send_message(message.from_user.id, "Кстати, у нас есть приложение в App Store)) скачивай! Там тоже удобный поиск)\nhttps://apps.apple.com/ru/app/getcoupon-купоны-и-акции/id1525623085")


@bot.message_handler(content_types=['text'])
def get(message):
    answer = get_coupon(message.text)
    bot.send_message(message.from_user.id, answer)


def get_coupon(text) -> str:
    shop = _search_for_shop(text,
                            all_shop_names,
                            all_shop_names_lower)

    if not shop:
        return f"Не найден '{text}' в базе данных("

    coupons: dict = _get_coupons(database, shop)

    if not coupons:
        return f"Купонов для '{shop}' не найдено("

    return _build_answer(coupons[0])


def _search_for_shop(user_text: str,
                     all_shop_names: list,
                     all_shop_names_lower: list) -> str:
    """
    Returns:
        str shopname if found
        '' if not found
    """

    text = user_text.lower()
    text = re.sub(r"[^a-zа-яё0-9\n \-]", " ", text)
    text = re.sub(r"[ ]+", " ", text)
    text = f" {text} "  # adding spaces for correct partial ratio searching

    for shop, shop_lowercase in zip(all_shop_names, all_shop_names_lower):
        partial_ratio = fuzz.partial_ratio(text, shop_lowercase)
        if partial_ratio > 82:
            return shop
    return ""


def _get_coupons(database, user_shop) -> 'dict | None':
    for shop in database:
        if shop['name'] == user_shop:
            return shop['promoCodes']
    return None


def _build_answer(coupon: dict) -> str:
    answer = f"{coupon['promoCodeDescription']}\n\nКупон: {coupon['coupon']}"
    return answer


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)

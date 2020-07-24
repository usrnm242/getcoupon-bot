import telebot

TOKEN = "1315357078:AAE9GQNe2cPVkqu2rOx5rPKnNlpUhOUaUNg"

bot = telebot.TeleBot(TOKEN)


def get_name(message):
    global name
    name = message.text
    bot.send_message(message.from_user.id, 'Какая у тебя фамилия?')
    bot.register_next_step_handler(message, get_surname)


def get_surname(message):
    global surname
    surname = message.text
    bot.send_message('Сколько тебе лет?')
    bot.register_next_step_handler(message, get_age)


def get_age(message):
    global age
    while age == 0:  # проверяем что возраст изменился
        try:
            age = int(message.text)  # проверяем, возраст введен корректно
        except Exception:
            bot.send_message(message.from_user.id, 'Цифрами, пожалуйста')
    bot.send_message(message.from_user.id, f"Тебе {age} лет, тебя зовут"
                                           f"{name} {surname}?")


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text in ("Привет", "Помощь", "Старт"):
        bot.send_message(message.from_user.id, "Привет, чем могу тебе помочь?")
    elif message.text == "/help":
        bot.send_message(message.from_user.id, "Напиши 'Привет'")
    else:
        bot.send_message(message.from_user.id, "Напиши /help.")


@bot.message_handler(content_types=['text'])
def start(message):
    if message.text == '/reg':
        bot.send_message(message.from_user.id, "Как тебя зовут?")
        bot.register_next_step_handler(message, get_name)
    else:
        bot.send_message(message.from_user.id, 'Напиши /reg')


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)

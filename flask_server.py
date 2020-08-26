from flask import Flask, request
from conf import WEBHOOK_HOST, WEBHOOK_URL_PATH
from getcoupon_bot import bot, telebot


app = Flask(__name__)


@app.route("/", methods=['POST'])
def index():
    json_from_tg = request.get_json()

    update = telebot.types.Update.de_json(json_from_tg)
    bot.process_new_updates([update])

    return 'ok'


bot.remove_webhook()
bot.set_webhook(url=f"{WEBHOOK_HOST}{WEBHOOK_URL_PATH}")


if __name__ == "__main__":
    app.run(debug=True)

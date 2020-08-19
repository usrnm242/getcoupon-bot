from flask import Flask, request
from flask_crontab import Crontab
from conf import WEBHOOK_HOST, WEBHOOK_URL_PATH
from getcoupon_bot import bot, telebot


app = Flask(__name__)
crontab = Crontab(app)


@app.route("/", methods=['POST'])
def index():
    try:
        json_from_tg = request.get_json()
    except Exception:
        return "fuck"

    update = telebot.types.Update.de_json(json_from_tg)
    bot.process_new_updates([update])

    return 'okay'


bot.remove_webhook()
bot.set_webhook(url=f"{WEBHOOK_HOST}{WEBHOOK_URL_PATH}")


if __name__ == "__main__":
    app.run(debug=True)

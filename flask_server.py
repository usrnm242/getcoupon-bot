from flask import Flask, request
from flask_crontab import Crontab

from conf import WEBHOOK_HOST, WEBHOOK_URL_PATH

# from getcoupon_bot import bot, telebot


app = Flask(__name__)
crontab = Crontab(app)


@app.route("/", methods=['POST'])
def index():
    try:
        json_from_tg = request.get_json()
    except Exception:
        return "fuck"

    # update = telebot.types.Update.de_json(json_from_tg)
    # bot.process_new_updates([update])

    return 'okay'


@crontab.job(minute="*/1")
def my_scheduled_job():
    print("OMG IT WORKS")


import datetime

db = {"time": datetime.datetime.now()}
exp = datetime.timedelta(seconds=3)


@app.route("/test", methods=['GET'])
def test():
    global db
    if datetime.datetime.now() - db['time'] > exp:
        print(f"CHANGED; old={db['time']}; new={datetime.datetime.now()}")
        db['time'] = datetime.datetime.now()
        print("ok")
    return 'ok'




# bot.remove_webhook()
# bot.set_webhook(url=f"{WEBHOOK_HOST}{WEBHOOK_URL_PATH}")


if __name__ == "__main__":
    app.run(debug=True)

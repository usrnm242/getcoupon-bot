from os import environ


TOKEN = environ.get('TOKEN', '')

DB_USER = environ.get('MYSQL_USER', 'root')
DB_PASSWORD = environ.get('MYSQL_PASSWORD', '')
DB_HOST = environ.get('MYSQL_HOST', 'localhost')

WEBHOOK_HOST = environ.get('SERVER_ADDR', "http://0.0.0.0:5000")
WEBHOOK_URL_PATH = "/getcoupon-bot-webhookie"

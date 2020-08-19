from os import environ


TOKEN = environ.get('TOKEN', '1315357078:AAE9GQNe2cPVkqu2rOx5rPKnNlpUhOUaUNg')

DB_USER = environ.get('MYSQL_USER', 'root')
DB_PASSWORD = environ.get('MYSQL_PASSWORD', 'dark3013')
DB_HOST = environ.get('MYSQL_HOST', 'localhost')

WEBHOOK_HOST = environ.get('SERVER_ADDR', "http://0.0.0.0:5000")
WEBHOOK_URL_PATH = "/getcoupon-bot-webhookie"

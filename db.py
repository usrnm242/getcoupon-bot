import peewee
import datetime
from conf import DB_USER, DB_PASSWORD, DB_HOST


db_last_update_time = datetime.datetime.now()


def update_db_if_needeed(func):

    def wrapper(*args, **kwargs):
        now = datetime.datetime.now()
        global db_last_update_time
        if now - db_last_update_time > datetime.timedelta(minutes=15):
            db_last_update_time = now
            save_to_sqlite_ram(get_db())

        return func(*args, **kwargs)

    return wrapper


memory_db_handle = peewee.SqliteDatabase(
    "coupons_and_users.db",
    pragmas={
        'cache_size': -1 * 16000,
        'foreign_keys': 1,
        'ignore_check_constraints': 0,
        'synchronous': 0
    })


class BotBaseModel(peewee.Model):
    class Meta:
        database = memory_db_handle


class BotShops(BotBaseModel):
    shop = peewee.CharField(max_length=90, unique=True, primary_key=True)
    alternative_name = peewee.CharField(max_length=30)
    shopname_lower = peewee.CharField(max_length=30)
    website_link = peewee.CharField()

    class Meta:
        db_table = 'bot_shops'


class BotCoupons(BotBaseModel):
    coupon = peewee.TextField(unique=True, primary_key=True)
    shop = peewee.ForeignKeyField(
        BotShops,
        to_field="shop",
        backref="coupons"
    )

    class Meta:
        db_table = 'bot_coupons'


class BotUsers(BotBaseModel):
    user_id = peewee.IntegerField(unique=True, primary_key=True)
    coupon_index = peewee.IntegerField(default=0)

    class Meta:
        db_table = 'bot_users'


def set_user_coupon_index(user_id: int, coupon_index: int = 0):
    try:
        q = BotUsers.replace(user_id=user_id, coupon_index=coupon_index)
        q.execute()
    except Exception as e:
        print(e)


def get_user_coupon_index(user_id: int):
    try:
        user, created = BotUsers.get_or_create(
            user_id=user_id,
            defaults={'coupon_index': 0}
        )
        return user.coupon_index
    except Exception as e:
        print(e)


def inc_user_coupon_index(user_id: int):
    _change_coupon_index(user_id, 1)


def dec_user_coupon_index(user_id: int):
    _change_coupon_index(user_id, -1)


def _change_coupon_index(user_id: int, diff: int):
    try:
        current_index = get_user_coupon_index(user_id)
        BotUsers.replace(
            user_id=user_id,
            coupon_index=current_index + diff
        ).execute()
    except Exception:
        BotUsers.replace(
            user_id=user_id,
            coupon_index=0
        ).execute()


def get_shops():
    return BotShops.select(BotShops.shop, BotShops.shopname_lower, BotShops.alternative_name)


@update_db_if_needeed
def get_coupons(shop: str) -> list:
    return BotShops.get(BotShops.shop == shop).coupons


dbhandle = peewee.MySQLDatabase(
    'promo',
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST
)


class BaseModel(peewee.Model):
    class Meta:
        database = dbhandle


class Shops(BaseModel):
    id = peewee.PrimaryKeyField(null=False)
    shop = peewee.CharField(max_length=50)
    alternative_name = peewee.CharField(max_length=30)
    website_link = peewee.CharField()
    affiliate_link = peewee.CharField(90)

    class Meta:
        db_table = "shops"
        order_by = ('id',)


class Coupons(BaseModel):
    id = peewee.PrimaryKeyField(null=False)
    promocode = peewee.CharField(max_length=40)
    adding_date = peewee.DateTimeField()
    expiration_date = peewee.DateTimeField()
    description = peewee.CharField(max_length=512)
    source = peewee.CharField(max_length=90)
    shop_id = peewee.ForeignKeyField(Shops, field="id")

    class Meta:
        db_table = "promocodes"
        order_by = ('id')


def _build_coupon(coupon) -> str:
    description = f"{coupon.description}\n\n" \
                  f"Промокод: {coupon.promocode}"

    def _add_zeros(date):
        if int(date) <= 9:
            return f"0{date}"
        else:
            return date

    if coupon.expiration_date - coupon.adding_date != \
            datetime.timedelta(days=10):
        date = coupon.expiration_date

        day = _add_zeros(date.day)

        month = _add_zeros(date.month)

        year = date.year % 2000

        description = f"{description}\n\n" \
                      f"Актуален до {day}.{month}.{year}"

    if coupon.source:
        description = f"{description}\n\nИсточник: {coupon.source}"

    return description


def _get_db() -> dict:
    dbhandle.connect(reuse_if_open=True)

    shops_list = []

    for shop in Shops.select():
        all_coupons_in_shop = \
            [_build_coupon(coupon) for coupon in
             Coupons.select().where(Coupons.shop_id == shop.id)]

        shop_dict = {
            'shop': shop.shop,
            'website_link': shop.affiliate_link if shop.affiliate_link else shop.website_link,
            'alternative_name': shop.alternative_name.lower(),
            'shopname_lower': shop.shop.lower(),
            'coupons': all_coupons_in_shop
        }

        shops_list.append(shop_dict)

    dbhandle.close()

    return shops_list


def get_db() -> dict:
    try:
        return _get_db()
    except peewee.InternalError as p:
        raise(p)


def save_to_sqlite_ram(db: list):
    try:
        memory_db_handle.connect(reuse_if_open=True)
        memory_db_handle.drop_tables([BotShops, BotCoupons])
        memory_db_handle.create_tables([BotShops, BotCoupons, BotUsers])

        BotShops.insert_many(
            db,
            fields=['shop', 'website_link',
                    'alternative_name', 'shopname_lower']
        ).execute()

        for shopdata in db:
            for coupon in shopdata['coupons']:
                coupon = BotCoupons.create(
                    coupon=coupon,
                    shop=shopdata['shop']
                )

    except peewee.InternalError as p:
        raise(p)


save_to_sqlite_ram(get_db())


if __name__ == '__main__':
    pass

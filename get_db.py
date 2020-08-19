import peewee
import datetime
from conf import DB_USER, DB_PASSWORD, DB_HOST


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
    shop_id = peewee.ForeignKeyField(Shops, field="id")

    class Meta:
        db_table = "promocodes"
        order_by = ('id')


def _build_coupon(coupon) -> str:
    description = f"{coupon.description}\n\n" \
                  f"Промокод: `{coupon.promocode}`"

    def _add_zeros(date):
        if int(date) < 9:
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

    return description


def _get_db() -> dict:
    dbhandle.connect(reuse_if_open=True)

    db_dict = {}

    for shop in Shops.select():
        all_coupons_in_shop = \
            [_build_coupon(coupon) for coupon in
             Coupons.select().where(Coupons.shop_id == shop.id)]

        db_dict[shop.shop] = \
            {'website_link': shop.affiliate_link if shop.affiliate_link else shop.website_link,
             'alternative_name': shop.alternative_name.lower(),
             'coupons': all_coupons_in_shop}

    dbhandle.close()

    return db_dict


def get_db() -> dict:
    try:
        return _get_db()
    except peewee.InternalError as p:
        raise(p)


if __name__ == '__main__':
    for key, val in get_db().items():
        print(key, val)

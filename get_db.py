import peewee


user = 'root'
password = 'dark3013'
db_name = 'promo'


dbhandle = peewee.MySQLDatabase(
    db_name,
    user=user,
    password=password,
    host='localhost'
)


class BaseModel(peewee.Model):
    class Meta:
        database = dbhandle


class Shops(BaseModel):
    id = peewee.PrimaryKeyField(null=False)
    shop = peewee.CharField(max_length=50)
    alternative_name = peewee.CharField(max_length=30)
    website_link = peewee.CharField()

    class Meta:
        db_table = "shops"
        order_by = ('id',)


class Coupons(BaseModel):
    id = peewee.PrimaryKeyField(null=False)
    promocode = peewee.CharField(max_length=40)
    expiration_date = peewee.DateTimeField()
    description = peewee.CharField(max_length=512)
    shop_id = peewee.ForeignKeyField(Shops, field="id")

    class Meta:
        db_table = "promocodes"
        order_by = ('id')


def _build_coupon(coupon) -> str:
    description = f"{coupon.description}\n\n" \
                  f"Актуален до {coupon.expiration_date}\n\n" \
                  f"Промокод: {coupon.promocode}"
    return description


def _get_db() -> dict:
    dbhandle.connect()

    db_dict = {}

    for shop in Shops.select():
        all_coupons_in_shop = \
            [_build_coupon(coupon) for coupon in
             Coupons.select().where(Coupons.shop_id == shop.id)]

        db_dict[shop.shop] = \
            {'website_link': shop.website_link,
             'alternative_name': shop.alternative_name.lower(),
             'coupons': all_coupons_in_shop}

    return db_dict


def get_db() -> dict:
    try:
        return _get_db()
    except peewee.InternalError as p:
        raise(p)


if __name__ == '__main__':
    for key, val in get_db().items():
        print(key, val)

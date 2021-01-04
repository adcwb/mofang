from application.utils.language.message import ErrorMessage as Message
from .models import Goods, db
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, auto_field
from marshmallow import post_dump


class GoodsInfoSchema(SQLAlchemyAutoSchema):
    id = auto_field()
    name = auto_field()
    price = auto_field()
    image = auto_field()
    remark = auto_field()
    credit = auto_field()

    class Meta:
        model = Goods
        fields = ["id", "name", "price", "image", "remark", "credit"]
        sql_session = db.session

    @post_dump()
    def mobile_format(self, data, **kwargs):
        data["price"] = "%.2f" % data["price"]
        if data["image"] == None:
            data["image"] = ""
        return data

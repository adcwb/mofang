from marshmallow_sqlalchemy import SQLAlchemyAutoSchema,auto_field
from .models import LiveStream,db
from application.apps.users.models import User
from marshmallow import post_dump
class StreamInfoSchema(SQLAlchemyAutoSchema):
    id = auto_field()
    name = auto_field()
    room_name = auto_field()
    user = auto_field()

    class Meta:
        model = LiveStream
        include_fk = True
        include_relationships = True
        fields = ["id","name","room_name","user"]
        sql_session = db.session

    @post_dump()
    def user_format(self, data, **kwargs):
        user = User.query.get(data["user"])
        if user is None:
            return data

        data["user"] = {
            "id":user.id,
            "nickname": user.nickname if user.nickname else "",
            "ip": user.ip_address if user.ip_address else "",
            "avatar": user.avatar if user.avatar else ""
        }
        return data
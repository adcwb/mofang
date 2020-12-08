from marshmallow import Schema, fields, validate, validates, ValidationError
from application.utils.language.message import ErrorMessage as Message
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, auto_field
from marshmallow import post_load, pre_load, validates_schema, post_dump
from .models import User, db
from application import redis


class MobileSchema(Schema):
    mobile = fields.String(required=True, validate=validate.Regexp("^1[3-9]\d{9}$", error=Message.mobile_format_error))

    @validates("mobile")
    def validates_mobile(self, data):
        user = User.query.filter(User.mobile == data).first()
        if user is not None:
            raise ValidationError(message=Message.mobile_is_use)
        return data


class UserSchema(SQLAlchemyAutoSchema):
    mobile = auto_field(required=True, load_only=True)
    password = fields.String(required=True, load_only=True)
    password2 = fields.String(required=True, load_only=True)
    sms_code = fields.String(required=True, load_only=True)

    class Meta:
        model = User
        include_fk = True  # 启用外键关系
        include_relationships = True  # 模型关系外部属性
        fields = ["id", "name", "mobile", "password", "password2", "sms_code"]  # 如果要全换全部字段，就不要声明fields或exclude字段即可
        sql_session = db.session

    @post_load()
    def save_object(self, data, **kwargs):
        data.pop("password2")
        data.pop("sms_code")
        data["name"] = data["mobile"]
        instance = User(**data)
        db.session.add(instance)
        db.session.commit()
        return instance

    @validates_schema
    def validate(self, data, **kwargs):
        # 校验密码和确认密码
        if data["password"] != data["password2"]:
            raise ValidationError(message=Message.password_not_match, field_name="password")

        # todo 校验短信验证码
        code = redis.get("sms_%s" % data.get("mobile"))

        if code is None:
            raise ValidationError(message=Message.sms_code_expired, field_name="sms_code")

        sms_code = str(code, encoding='utf-8')

        if sms_code != data.get("sms_code"):
            raise ValidationError(message=Message.sms_code_error, field_name="sms_code")

        redis.delete("sms_%s" % data["mobile"])

        return data


class UserInfoSchema(SQLAlchemyAutoSchema):
    id = auto_field()
    mobile = auto_field()
    nickname = auto_field()
    avatar = auto_field()

    class Meta:
        model = User
        include_fk = True
        include_relationships = True
        fields = ["id", "mobile", "nickname", "avatar"]
        sql_session = db.session

    @post_dump()
    def mobile_format(self, data, **kwargs):
        data["mobile"] = data["mobile"][:3] + "****" + data["mobile"][-4:]
        return data

from marshmallow import Schema, fields, validate, validates, ValidationError
from application.utils.language.message import ErrorMessage as Message
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, auto_field
from marshmallow import post_load, pre_load, validates_schema, post_dump
from .models import User, db, UserRelation
from application import redis
from sqlalchemy import or_, and_
from application import mongo
from datetime import datetime


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
    invite_uid = fields.Integer(required=True, load_only=True)

    class Meta:
        model = User
        include_fk = True  # 启用外键关系
        include_relationships = True  # 模型关系外部属性
        fields = ["id", "name", "mobile", "password", "password2", "sms_code",
                  "invite_uid"]  # 如果要全换全部字段，就不要声明fields或exclude字段即可
        sql_session = db.session

    @post_load()
    def save_object(self, data, **kwargs):
        invite_uid = int(data["invite_uid"])
        data.pop("password2")
        data.pop("sms_code")
        data.pop("invite_uid")
        data["name"] = data["mobile"]
        instance = User(**data)
        db.session.add(instance)
        db.session.commit()

        # 记录邀请信息到Mongdb中
        if invite_uid > 0:
            """只有invite_uid大于0，才是经过邀请注册进来的新用户"""
            # 验证是否属于有效的邀请
            invite_user = User.query.get(invite_uid)
            if invite_user is not None:
                """只有邀请人存在的情况下才算有效邀请"""
                query = {"_id": invite_uid}
                ret = mongo.db.user_invite_list.find_one(query)
                if ret:
                    mongo.db.user_invite_list.update(query, {"$push": {"invite_list": instance.id}})
                else:
                    data = {"_id": invite_uid, "invited_list": [instance.id]}
                    mongo.db.user_invite_list.insert(data)
                # 添加好友关系

        return instance

    @validates_schema
    def validate(self, data, **kwargs):
        # 校验密码和确认密码
        if data["password"] != data["password2"]:
            raise ValidationError(message=Message.password_not_match, field_name="password")

        # 校验短信验证码
        # 1. 从redis中提取验证码
        redis_sms_code = redis.get("sms_%s" % data["mobile"])
        if redis_sms_code is None:
            raise ValidationError(message=Message.sms_code_expired, field_name="sms_code")
        redis_sms_code = redis_sms_code.decode()
        # 2. 从客户端提交的数据data中提取验证码
        sms_code = data["sms_code"]
        # 3. 字符串比较，如果失败，则抛出异常，否则，直接删除验证码
        if sms_code != redis_sms_code:
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


class ChangePassword(SQLAlchemyAutoSchema):
    mobile = auto_field(required=True, load_only=True)
    password = fields.String(required=True, load_only=True)
    password2 = fields.String(required=True, load_only=True)
    sms_code = fields.String(required=True, load_only=True)

    class Meta:
        model = User
        include_fk = True  # 启用外键关系
        include_relationships = True  # 模型关系外部属性
        sql_session = db.session

    @validates_schema
    def validate(self, data, **kwargs):
        # 校验密码和确认密码

        if data["password"] != data["password2"]:
            raise ValidationError(message=Message.password_not_match, field_name="password")

        # 校验短信验证码
        code = redis.get("sms_%s" % data.get("mobile"))

        if code is None:
            raise ValidationError(message=Message.sms_code_expired, field_name="sms_code")
        sms_code = str(code, encoding='utf-8')
        if sms_code != data.get("sms_code"):
            raise ValidationError(message=Message.sms_code_error, field_name="sms_code")
        redis.delete("sms_%s" % data["mobile"])

        # 保存新密码
        user = User.query.filter(User.mobile == data["mobile"]).first()
        user.password = data["password"]
        db.session.commit()

        return data


class UserSearchInfoSchema(SQLAlchemyAutoSchema):
    """用户搜索信息返回"""
    id = auto_field()
    nickname = auto_field()
    avatar = auto_field()
    relation_status = fields.String(dump_only=True)

    @post_dump()
    def relation_status_post(self, data, **kwargs):
        relaionship = UserRelation.query.filter(
            or_(
                and_(UserRelation.send_user == self.context["user_id"], UserRelation.receive_user == data["id"]),
                and_(UserRelation.receive_user == self.context["user_id"], UserRelation.send_user == data["id"]),
            )
        ).first()
        if relaionship is not None and relaionship.relation_status == 1:
            """判断当前双方是否是好友"""
            data["relation_status"] = UserRelation.relation_status_chioce[relaionship.relation_status - 1]
        else:
            # 判断当前用户是否曾经添加过对方
            query = {
                "$or": [{
                    "$and": [
                        {
                            "send_user_id": self.context["user_id"],
                            "receive_user_id": data["id"],
                            "time": {"$gte": datetime.now().timestamp() - 60 * 60 * 24 * 7}
                        }
                    ],
                }, {
                    "$and": [
                        {
                            "send_user_id": data["id"],
                            "receive_user_id": self.context["user_id"],
                            "time": {"$gte": datetime.now().timestamp() - 60 * 60 * 24 * 7}
                        }
                    ],
                }]
            }
            document_list = mongo.db.user_relation_history.find(query, {"_id": 0}).sort("time", -1)
            document = [document for document in document_list]
            print(document)
            if len(document) > 0:
                document = document[0]
                if document.get("send_user_id") == self.context["user_id"]:
                    if document.get("status") == 0:
                        data["relation_status"] = (0, "已添加")
                    elif document.get("status") == 1:
                        data["relation_status"] = (1, "已通过")
                    elif document.get("status") == 2:
                        data["relation_status"] = (2, "已拒绝")
                    else:
                        data["relation_status"] = (3, "已取消")
                else:
                    if document.get("status") == 0:
                        data["relation_status"] = (0, "等待通过")
                    elif document.get("status") == 1:
                        data["relation_status"] = (1, "已通过")
                    elif document.get("status") == 2:
                        data["relation_status"] = (2, "已拒绝")
                    else:
                        data["relation_status"] = (3, "已取消")
            else:
                data["relation_status"] = (0, "添加")

        return data

    class Meta:
        model = User
        include_fk = True
        include_relationships = True
        fields = ["id", "nickname", "avatar", "relation_status"]
        sql_session = db.session

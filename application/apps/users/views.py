from application import jsonrpc, db
from .marshmallow import MobileSchema, UserSchema
from marshmallow import ValidationError
from application.utils.language.message import ErrorMessage as Message
from application.utils.language.status import APIStatus as status


@jsonrpc.method("User.mobile")
def mobile(mobile):
    """验证手机号码是否已经注册"""
    ms = MobileSchema()
    try:
        ms.load({"mobile": mobile})
        ret = {"errno": status.CODE_OK, "errmsg": Message.ok}
    except ValidationError as e:
        ret = {"errno": status.CODE_VALIDATE_ERROR, "errmsg": e.messages["mobile"][0]}
    return ret


@jsonrpc.method("User.register")
def register(mobile, password, password2, sms_code):
    """用户信息注册"""

    try:
        ms = MobileSchema()
        ms.load({"mobile": mobile})

        us = UserSchema()
        user = us.load({
            "mobile": mobile,
            "password": password,
            "password2": password2,
            "sms_code": sms_code
        })
        data = {"errno": status.CODE_OK, "errmsg": us.dump(user)}
    except ValidationError as e:
        data = {"errno": status.CODE_VALIDATE_ERROR, "errmsg": e.messages}
    return data

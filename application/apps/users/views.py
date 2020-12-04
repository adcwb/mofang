from flask import jsonify, json
from sqlalchemy import or_
from .models import User
from flask import current_app, request
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, \
    jwt_refresh_token_required

from application import jsonrpc, db
from .marshmallow import MobileSchema, UserSchema
from marshmallow import ValidationError
from application.utils.language.message import ErrorMessage as message
from application.utils.language.status import APIStatus as status
from urllib.parse import urlencode
from urllib.request import urlopen

@jsonrpc.method("User.mobile")
def mobile(mobile):
    """验证手机号码是否已经注册"""
    ms = MobileSchema()
    try:
        ms.load({"mobile": mobile})
        ret = {"errno": status.CODE_OK, "errmsg": message.ok}
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


@jsonrpc.method("User.login")
def login(ticket, randstr, account, password):
    """根据用户登录信息生成token"""

    # 校验防水墙验证码
    params = {
        "aid": current_app.config.get("CAPTCHA_APP_ID"),
        "AppSecretKey": current_app.config.get("CAPTCHA_APP_SECRET_KEY"),
        "Ticket": ticket,
        "Randstr": randstr ,
        "UserIP": request.remote_addr,
    }
    # 把字典数据转换成地址栏的查询字符串格式
    # aid=xxx&AppSecretKey=xxx&xxxxx
    params = urlencode(params)
    url = current_app.config.get("CAPTCHA_GATEWAY")
    # 发送http的get请求
    f = urlopen("%s?%s" % (url, params))
    # https://ssl.captcha.qq.com/ticket/verify?aid=xxx&AppSecretKey=xxx&xxxxx

    content = f.read()
    res = json.loads(content)
    print(res)

    if int(res.get("response")) != 1:
        # 验证失败
        return {"errno": status.CODE_CAPTCHA_ERROR, "errmsg": message.captcaht_no_match}


    # 1. 根据账户信息和密码获取用户
    if len(account) < 1:
        return {"errno": status.CODE_NO_ACCOUNT, "errmsg": message.account_no_data}
    user = User.query.filter(or_(
        User.mobile == account,
        User.email == account,
        User.name == account
    )).first()

    if user is None:
        return {"errno": status.CODE_NO_USER, "errmsg": message.user_not_exists}

    # 验证密码
    if not user.check_password(password):
        return {"errno": status.CODE_PASSWORD_ERROR, "errmsg": message.password_error}

    # 2. 生成jwt token
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    print(access_token)
    print(refresh_token)
    return {"access_token": access_token, "refresh_token": refresh_token}


@jsonrpc.method("User.info")
@jwt_required  # 验证jwt
def info():
    """获取用户信息"""
    user_data = json.loads(get_jwt_identity())  # get_jwt_identity 用于获取载荷中的数据
    print(user_data)
    return "ok"


@jsonrpc.method("User.refresh")
@jwt_refresh_token_required
def refresh():
    """重新获取新的认证令牌token"""
    current_user = get_jwt_identity()
    # 重新生成token
    access_token = create_access_token(identity=current_user)
    return access_token

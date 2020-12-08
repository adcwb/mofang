import requests
import base64
import uuid
import os
from flask import jsonify, json
from sqlalchemy import or_
from .models import User
from flask import current_app, request, make_response
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, \
    jwt_refresh_token_required

from application import jsonrpc, db
from .marshmallow import MobileSchema, UserSchema, UserInfoSchema
from marshmallow import ValidationError
from application.utils.language.message import ErrorMessage as message
from application.utils.language.status import APIStatus as status
from urllib.parse import urlencode
from urllib.request import urlopen


@jsonrpc.method("User.avatar.update")
@jwt_required  # 验证jwt
def update_avatar(avatar):
    """
    更新用户头像
    :param avatar:
    :return:
    """
    # 1.接收客户端上传的头像信息
    ext = avatar[avatar.find("/") + 1:avatar.find(";")]  # 资源格式
    b64_avatar = avatar[avatar.find(",") + 1:]
    b64_image = base64.b64decode(b64_avatar)
    filename = uuid.uuid4()
    static_path = os.path.join(current_app.BASE_DIR, current_app.config["STATIC_DIR"])
    print(static_path)
    with open("%s/%s.%s" % (static_path, filename, ext), "wb") as f:
        f.write(b64_image)

    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if user is None:
        return {
            "errno": status.CODE_NO_USER,
            "errmsg": message.user_not_exists,
        }
    # 判断用户是否上传文件过程中取消,
    if ext == "":
        return {
            "errno": status.AVATAR_ERROR,
            "errmsg": message.avatar_save_error
        }

    user.avatar = "%s.%s" % (filename, ext)
    db.session.commit()
    return {
        "errno": status.CODE_OK,
        "errmsg": message.avatar_save_success,
        "avatar": "%s.%s" % (filename, ext)
    }


@jwt_required  # 验证jwt
def avatar():
    """获取头像信息"""
    avatar = request.args.get("sign")
    ext = avatar[avatar.find(".") + 1:]
    filename = avatar[:avatar.find(".")]
    static_path = os.path.join(current_app.BASE_DIR, current_app.config["STATIC_DIR"])
    with open("%s/%s.%s" % (static_path, filename, ext), "rb") as f:
        content = f.read()
    response = make_response(content)
    response.headers["Content-Type"] = "image/%s" % ext
    return response


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
        "Randstr": randstr,
        "UserIP": request.remote_addr,
    }
    # 把字典数据转换成地址栏的查询字符串格式
    # aid=xxx&AppSecretKey=xxx&xxxxx
    print(params)
    params = urlencode(params)
    print(">>>>", params)

    url = current_app.config.get("CAPTCHA_GATEWAY")
    # 发送http的get请求
    # f = urlopen("%s?%s" % (url, params))
    # https://ssl.captcha.qq.com/ticket/verify?aid=xxx&AppSecretKey=xxx&xxxxx
    # content = f.read()
    # res = json.loads(content)
    # print(res)

    f = requests.get(url, params=params)
    # < Response[200] >
    # <class 'requests.models.Response'>
    # {'response': '1', 'evil_level': '0', 'err_msg': 'OK'}
    res = f.json()
    print(res)
    print(">>>>>", res.get("response"))
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
    return {
        "errno": status.CODE_OK,
        "errmsg": message.ok,
        "id": user.id,
        "nickname": user.nickname if user.nickname else account,
        "access_token": access_token,
        "refresh_token": refresh_token
    }


@jsonrpc.method("User.info")
@jwt_required  # 验证jwt
def info():
    """获取用户信息"""
    current_user_id = get_jwt_identity()  # get_jwt_identity 用于获取载荷中的数据
    user = User.query.get(current_user_id)
    if user is None:
        return {
            "errno": status.CODE_NO_USER,
            "errmsg": message.user_not_exists,
        }
    uis = UserInfoSchema()
    data = uis.dump(user)
    return {
        "errno": status.CODE_OK,
        "errmsg": message.ok,
        **data
    }



@jsonrpc.method("User.refresh")
@jwt_refresh_token_required
def refresh():
    """重新获取新的认证令牌token"""
    current_user = get_jwt_identity()
    # 重新生成token
    access_token = create_access_token(identity=current_user)
    return access_token




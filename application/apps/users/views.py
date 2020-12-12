import requests
import base64
import uuid
import os
from datetime import datetime
from flask import jsonify, json
from sqlalchemy import or_
from .models import User
from flask import current_app, request, make_response
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, \
    jwt_refresh_token_required

from application import jsonrpc, db, mongo, redis
from .marshmallow import MobileSchema, UserSchema, UserInfoSchema
from marshmallow import ValidationError
from application.utils.language.message import ErrorMessage as message
from application.utils.language.status import APIStatus as status
from urllib.parse import urlencode
from urllib.request import urlopen


@jsonrpc.method("User.avatar.update")
@jwt_required  # 验证jwt
def update_avatar(avatar):
    """获取用户信息"""
    # 1. 接受客户端上传的头像信息
    ext = avatar[avatar.find("/") + 1:avatar.find(";")]  # 资源格式
    b64_avatar = avatar[avatar.find(",") + 1:]
    b64_image = base64.b64decode(b64_avatar)
    filename = uuid.uuid4()
    static_path = os.path.join(current_app.BASE_DIR, current_app.config["STATIC_DIR"])
    with open("%s/%s.%s" % (static_path, filename, ext), "wb") as f:
        f.write(b64_image)

    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if user is None:
        return {
            "errno": status.CODE_NO_USER,
            "errmsg": message.user_not_exists,
        }
    user.avatar = "%s.%s" % (filename, ext)
    db.session.commit()
    # 添加修改记录！
    document = {
        "user_id": user.id,
        "user_name": user.name,
        "user_nikcname": user.nickname,
        "updated_time": datetime.now().timestamp(),  # 修改时间
        "avatar": avatar,  # 图片内容
        "type": "avatar",  # 本次操作的类型
    }
    mongo.db.user_info_history.insert_one(document)

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


@jsonrpc.method("User.check")
@jwt_required  # 验证jwt
def check():
    return {
        "errno": status.CODE_OK,
        "errmsg": message.ok,
    }


@jsonrpc.method("User.refresh")
@jwt_refresh_token_required  # 验证refresh_token
def refresh():
    """重新获取新的认证令牌token"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if user is None:
        return {
            "errno": status.CODE_NO_USER,
            "errmsg": message.user_not_exists,
        }

    # 重新生成token
    access_token = create_access_token(identity=current_user_id)
    return {
        "errno": status.CODE_OK,
        "errmsg": message.ok,
        "access_token": access_token
    }


@jsonrpc.method("User.transaction.password")
@jwt_required  # 验证jwt
def transaction_password(password1, password2, old_password=None):
    """
    交易密码的初始化和修改
    1. 刚注册的用户，没有交易密码，所以此处填写的是新密码
    2. 已经有了交易密码的用户，修改旧的交易密码
    :param password1:
    :param password2:
    :param old_password:
    :return:
    """

    if password1 != password2:
        return {
            "errno": status.CODE_TRANSACTION_PASSWORD_ERROR,
            "errmsg": message.transaction_password_not_match
        }
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if user is None:
        return {
            "errno": status.CODE_NO_USER,
            "errmsg": message.user_not_exists,
        }

    # 如果之前有存在交易密码，则需要验证旧密码
    if user.transaction_password:
        """修改"""
        # 验证旧密码
        ret = user.check_transaction_password(old_password)
        if ret == False:
            return {
                "errno": status.CODE_PASSWORD_ERROR,
                "errmsg": message.transaction_password_error
            }

    # 设置交易密码
    user.transaction_password = password1
    db.session.commit()

    # 添加交易密码的修改记录，为了保证安全，仅仅记录旧密码！
    if old_password:
        document = {
            "user_id": user.id,
            "user_name": user.name,
            "user_nikcname": user.nickname,
            "updated_time": datetime.now().timestamp(),  # 修改时间
            "transaction_password": old_password,  # 变更内容
            "type": "transaction_password",  # 本次操作的类型
        }

        mongo.db.user_info_history.insert_one(document)

    return {
        "errno": status.CODE_OK,
        "errmsg": message.ok
    }


@jsonrpc.method("User.change.nickname")
@jwt_required  # 验证jwt
def change_nickname(nickname):
    """
    用户昵称修改
    :param nickname: 用户昵称
    :return:
    """
    if nickname == "":
        return {
            "errno": status.NICKNAME_NULL,
            "errmsg": message.nickname_null
        }

    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if user is None:
        return {
            "errno": status.CODE_NO_USER,
            "errmsg": message.user_not_exists,
        }

    user.nickname = nickname
    db.session.commit()

    return {
        "errno": status.CODE_OK,
        "errmsg": message.avatar_save_success,
        "nickname": nickname,
    }


@jsonrpc.method("User.change.password")
@jwt_required  # 验证jwt
def change_login_password(old_pwd, new_pwd):
    """
    用户登录密码修改接口
    :param old_pwd: 旧密码
    :param new_pwd: 新密码
    :return: 返回前端的内容
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if user is None:
        return {
            "errno": status.CODE_NO_USER,
            "errmsg": message.user_not_exists,
        }
    ret = user.check_password(old_pwd)
    if ret == False:
        return {
            "errno": status.CODE_PASSWORD_ERROR,
            "errmsg": message.password_error
        }

    if old_pwd == new_pwd:
        return {
            "errno": status.CHANGE_PASSWD_ERROR,
            "errmsg": message.password_change_error
        }

    user.password = new_pwd
    db.session.commit()

    return {
        "errno": status.CODE_OK,
        "errmsg": message.password_change_success,
    }


@jsonrpc.method("User.forget.password")
def forget_password(mobile, sms_code, password, req_password):
    """
    密码修改接口
    :param moblie:
    :param sms_code:
    :param password:
    :param req_password:
    :return:
    """

    if password != req_password:
        raise ValidationError(message=message.password_not_match, field_name="password")

    # 校验短信验证码
    code = redis.get("sms_%s" % mobile)

    if code is None:
        raise ValidationError(message=message.sms_code_expired, field_name="sms_code")

    sms_code1 = str(code, encoding='utf-8')

    if sms_code1 != sms_code:
        raise ValidationError(message=message.sms_code_error, field_name="sms_code")

    redis.delete("sms_%s" % mobile)
    print(">>>>>>>>>>>>>>>>>>>>>>>>>",mobile)
    user = User.query.filter(User.mobile == mobile).first()
    print(">>>>>>>>>>>>>>>>>>>>>>>>>",user)
    user.password = password
    db.session.commit()

    return {
        "errno": status.CODE_OK,
        "errmsg": message.password_change_success,
    }


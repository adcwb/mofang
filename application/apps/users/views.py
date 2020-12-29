import decimal
import requests
import base64
import uuid
import os
import json
import random
from datetime import datetime

from sqlalchemy import or_, and_
from .models import User, UserRelation, Recharge
from flask import current_app, request, make_response, render_template
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, \
    jwt_refresh_token_required

from application import jsonrpc, db, mongo, redis, QRCode
from .marshmallow import MobileSchema, UserSchema, UserInfoSchema, ChangePassword, UserSearchInfoSchema as usis
from marshmallow import ValidationError
from application.utils.language.message import ErrorMessage as message
from application.utils.language.status import APIStatus as status
from urllib.parse import urlencode
from alipay import AliPay
from alipay.utils import AliPayConfig


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
    file = "%s/%s.%s" % (static_path, filename, ext)
    if not os.path.isfile(file):
        ext = "jpeg"
        file = "%s/%s.%s" % (static_path, "822ed419-1e9c-49b6-841e-fa604bfc071b", ext)  # 在配置文件中设置为默认头像即可
    with open(file, "rb") as f:
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
def register(mobile, password, password2, sms_code, invite_uid):
    """用户信息注册"""
    try:
        ms = MobileSchema()
        ms.load({"mobile": mobile})

        us = UserSchema()
        user = us.load({
            "mobile": mobile,
            "password": password,
            "password2": password2,
            "sms_code": sms_code,
            "invite_uid": invite_uid,
        })
        data = {"errno": status.CODE_OK, "errmsg": us.dump(user)}
    except ValidationError as e:
        data = {"errno": status.CODE_VALIDATE_ERROR, "errmsg": e.messages}
    return data


@jsonrpc.method("User.login")
def login(ticket, randstr, account, password):
    """根据用户登录信息生成token"""

    # 校验防水墙验证码
    # params = {
    #     "aid": current_app.config.get("CAPTCHA_APP_ID"),
    #     "AppSecretKey": current_app.config.get("CAPTCHA_APP_SECRET_KEY"),
    #     "Ticket": ticket,
    #     "Randstr": randstr,
    #     "UserIP": request.remote_addr,
    # }
    # # 把字典数据转换成地址栏的查询字符串格式
    # # aid=xxx&AppSecretKey=xxx&xxxxx
    # print(params)
    # print("12345666")
    # params = urlencode(params)
    # print(">>>>", params)
    #
    # url = current_app.config.get("CAPTCHA_GATEWAY")
    # # 发送http的get请求
    # # f = urlopen("%s?%s" % (url, params))
    # # https://ssl.captcha.qq.com/ticket/verify?aid=xxx&AppSecretKey=xxx&xxxxx
    # # content = f.read()
    # # res = json.loads(content)
    # # print(res)
    #
    # f = requests.get(url, params=params)
    # # < Response[200] >
    # # <class 'requests.models.Response'>
    # # {'response': '1', 'evil_level': '0', 'err_msg': 'OK'}
    # res = f.json()
    # print(res)
    # print(">>>>>", res.get("response"))
    # if int(res.get("response")) != 1:
    #     # 验证失败
    #
    #     return {"errno": status.CODE_CAPTCHA_ERROR, "errmsg": message.captcaht_no_match}

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
        "avatar": user.avatar if user.avatar else current_app.config["DEFAULT_AVATAR"],
        "money": float("%.2f" % user.money),
        "credit": user.credit,
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
        "money": float("%.2f" % user.money),
        "credit": user.credit,
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
    :param moblie: 手机号码
    :param sms_code:　验证码
    :param password:　新密码
    :param req_password:　确认新密码
    :return:
    """

    try:

        change_password = ChangePassword()
        change_password.load({
            "mobile": mobile,
            "password": password,
            "password2": req_password,
            "sms_code": sms_code
        })
        data = {"errno": status.CODE_OK, "errmsg": message.password_change_success, }
    except ValidationError as e:
        data = {"errno": status.CODE_VALIDATE_ERROR, "errmsg": e.messages}
    return data


@jsonrpc.method("User.user.relation")
@jwt_required  # 验证jwt
def user_relation(account):
    """搜索用户信息"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if user is None:
        return {
            "errno": status.CODE_NO_USER,
            "errmsg": message.user_not_exists,
        }

    # 1. 识别搜索用户
    receive_user_list = User.query.filter(or_(
        User.mobile == account,
        User.name == account,
        User.nickname.contains(account),
        User.email == account
    )).all()

    if len(receive_user_list) < 1:
        return {
            "errno": status.CODE_NO_USER,
            "errmsg": message.receive_user_not_exists,
        }
    # context 可用于把视图中的数据传递给marshmallow转换器中使用
    marshmallow = usis(many=True, context={"user_id": user.id})
    user_list = marshmallow.dump(receive_user_list)
    return {
        "errno": status.CODE_OK,
        "errmsg": message.ok,
        "user_list": user_list
    }


@jsonrpc.method("User.friend.add")
@jwt_required  # 验证jwt
def add_friend_apply(user_id):
    """申请添加好友"""
    print(user_id)
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if user is None:
        return {
            "errno": status.CODE_NO_USER,
            "errmsg": message.user_not_exists,
        }

    receive_user = User.query.get(user_id)
    if receive_user is None:
        return {
            "errno": status.CODE_NO_USER,
            "errmsg": message.receive_user_not_exists,
        }

    # 查看是否被对方拉黑了

    # 添加一个申请记录
    document = {
        "send_user_id": user.id,
        "send_user_nickname": user.nickname,
        "send_user_avatar": user.avatar,
        "receive_user_id": receive_user.id,
        "receive_user_nickname": receive_user.nickname,
        "receive_user_avatar": receive_user.avatar,
        "time": datetime.now().timestamp(),  # 操作时间
        "status": 0,
    }
    mongo.db.user_relation_history.insert_one(document)
    return {
        "errno": status.CODE_OK,
        "errmsg": message.ok,
    }


@jsonrpc.method("User.friend.apply")
@jwt_required  # 验证jwt
def add_friend_apply(user_id, agree, search_text):
    """处理好友申请"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if user is None:
        return {
            "errno": status.CODE_NO_USER,
            "errmsg": message.user_not_exists,
        }

    receive_user = User.query.get(user_id)
    if receive_user is None:
        return {
            "errno": status.CODE_NO_USER,
            "errmsg": message.receive_user_not_exists,
        }

    relaionship = UserRelation.query.filter(
        or_(
            and_(UserRelation.send_user == user.id, UserRelation.receive_user == receive_user.id),
            and_(UserRelation.receive_user == user.id, UserRelation.send_user == receive_user.id),
        )
    ).first()

    if agree:
        if receive_user.mobile == search_text:
            chioce = 0
        elif receive_user.name == search_text:
            chioce = 1
        elif receive_user.email == search_text:
            chioce = 2
        elif receive_user.nickname == search_text:
            chioce = 3
        else:
            chioce = 4

        if relaionship is not None:
            relaionship.relation_status = 1
            relaionship.relation_type = chioce
            db.session.commit()
        else:
            relaionship = UserRelation(
                send_user=user.id,
                receive_user=receive_user.id,
                relation_status=1,
                relation_type=chioce,
            )
            db.session.add(relaionship)
            db.session.commit()

    # 调整mongoDB中用户关系的记录状态
    query = {
        "$or": [{
            "$and": [
                {
                    "send_user_id": user.id,
                    "receive_user_id": receive_user.id,
                    "time": {"$gte": datetime.now().timestamp() - 60 * 60 * 24 * 7}
                }
            ],
        }, {
            "$and": [
                {
                    "send_user_id": receive_user.id,
                    "receive_user_id": user.id,
                    "time": {"$gte": datetime.now().timestamp() - 60 * 60 * 24 * 7}
                }
            ],
        }]
    }
    if agree:
        argee_status = 1
    else:
        argee_status = 2

    ret = mongo.db.user_relation_history.update(query, {"$set": {"status": argee_status}})
    if ret and ret.get("nModified") < 1:
        return {
            "errno": status.CODE_UPDATE_USER_RELATION_ERROR,
            "errmsg": message.update_user_relation_fail,
        }
    else:
        return {
            "errno": status.CODE_OK,
            "errmsg": message.update_success,
        }


@jsonrpc.method("User.relation.history")
@jwt_required  # 验证jwt
def history_relation():
    """查找好友关系历史记录"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if user is None:
        return {
            "errno": status.CODE_NO_USER,
            "errmsg": message.user_not_exists,
        }

    query = {
        "$or": [
            {"send_user_id": user.id, "time": {"$gte": datetime.now().timestamp() - 60 * 60 * 24 * 7}},
            {"receive_user_id": user.id, "time": {"$gte": datetime.now().timestamp() - 60 * 60 * 24 * 7}},
        ]
    }
    document_list = mongo.db.user_relation_history.find(query, {"_id": 0})
    data_list = []
    for document in document_list:
        if document.get("send_user_id") == user.id and document.get("status") == 0:
            document["status"] = (0, "已添加")
        elif document.get("receive_user_id") == user.id and document.get("status") == 0:
            document["status"] = (0, "等待通过")
        elif document.get("status") == 1:
            document["status"] = (1, "已通过")
        else:
            document["status"] = (2, "已拒绝")

        data_list.append(document)

    return {
        "errno": status.CODE_OK,
        "errmsg": message.ok,
        "data_list": data_list,
    }


@jsonrpc.method("User.friend.list")
@jwt_required  # 验证jwt
def list_friend(page=1, limit=2):
    """好友列表"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if user is None:
        return {
            "errno": status.CODE_NO_USER,
            "errmsg": message.user_not_exists,
        }

    pagination = UserRelation.query.filter(
        or_(
            and_(UserRelation.send_user == user.id),
            and_(UserRelation.receive_user == user.id),
        )
    ).paginate(page, per_page=limit)
    user_id_list = []
    # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    # print(pagination.items)
    # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    for relation in pagination.items:
        if relation.send_user == user.id:
            user_id_list.append(relation.receive_user)
        else:
            user_id_list.append(relation.send_user)

    # 获取用户详细信息
    # print(">>>>>>>>>>>>>>>>１>>>>>>>>>>>>>>>>>")
    # print(user_id_list)
    # print(">>>>>>>>>>>>>>>>１>>>>>>>>>>>>>>>>>")
    user_list = User.query.filter(User.id.in_(user_id_list)).all()
    friend_list = [{"avatar": user.avatar, "nickname": user.nickname, "id": user.id, "fruit": 0, "fruit_status": 0} for
                   user in user_list]
    pages = pagination.pages
    # print(">>>>>>>>>>>>>>>>２>>>>>>>>>>>>>>>>>")
    # print(friend_list)
    # print(">>>>>>>>>>>>>>>>２>>>>>>>>>>>>>>>>>")
    return {
        "errno": status.CODE_OK,
        "errmsg": message.ok,
        "friend_list": friend_list,
        "pages": pages
    }


@jwt_required  # 验证jwt
def invite_code():
    """邀请好友的二维码"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if user is None:
        return {
            "errno": status.CODE_NO_USER,
            "errmsg": message.user_not_exists,
        }
    static_path = os.path.join(current_app.BASE_DIR, current_app.config["STATIC_DIR"])
    if not user.avatar:
        user.avatar = current_app.config["DEFAULT_AVATAR"]
    avatar = static_path + "/" + user.avatar
    data = current_app.config.get("SERVER_URL",
                                  request.host_url[:-1]) + "/users/invite/download?uid=%s" % current_user_id
    image = QRCode.qrcode(data, box_size=16, icon_img=avatar)
    b64_image = image[image.find(",") + 1:]
    qrcode_iamge = base64.b64decode(b64_image)
    response = make_response(qrcode_iamge)
    response.headers["Content-Type"] = "image/png"
    return response


def invite_download():
    uid = request.args.get("uid")
    if "micromessenger" in request.headers.get("User-Agent").lower():
        position = "weixin"
    else:
        position = "other"

    return render_template("user/download.html", position=position, uid=uid)


@jsonrpc.method("User.change_mobile")
@jwt_required  # 验证jwt
def list_friend(ticket, randstr, old_mobile, new_mobile, sms_code):
    # 校验防水墙验证码
    params = {
        "aid": current_app.config.get("CAPTCHA_APP_ID"),
        "AppSecretKey": current_app.config.get("CAPTCHA_APP_SECRET_KEY"),
        "Ticket": ticket,
        "Randstr": randstr,
        "UserIP": request.remote_addr,
    }
    # 把字典数据转换成地址栏的查询字符串格式

    params = urlencode(params)
    url = current_app.config.get("CAPTCHA_GATEWAY")
    f = requests.get(url, params=params)
    res = f.json()
    if int(res.get("response")) != 1:
        # 验证失败
        return {"errno": status.CODE_CAPTCHA_ERROR, "errmsg": message.captcaht_no_match}

    # 查询当前登录用户
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    # print(">>>>", user)     # <User: 17319006603>
    # print(">>>>", user.mobile, type(user.mobile))   # 17319006603 <class 'str'>

    if user is None:
        return {
            "errno": status.CODE_NO_USER,
            "errmsg": message.user_not_exists,
        }
    if old_mobile == new_mobile:
        return {
            "errno": status.CHANGE_PASSWD_ERROR,
            "errmsg": message.password_change_error,
        }
    elif user.mobile != old_mobile:
        return {
            "errno": status.CODE_NO_ACCOUNT,
            "errmsg": message.mobile_is_null,
        }

    # 校验短信验证码
    # 1. 从redis中提取验证码
    redis_sms_code = redis.get("sms_%s" % old_mobile)
    if redis_sms_code is None:
        raise ValidationError(message=message.sms_code_expired, field_name="sms_code")
    redis_sms_code = redis_sms_code.decode()
    # 2. 从客户端提交的数据data中提取验证码
    sms_code = sms_code
    # 3. 字符串比较，如果失败，则抛出异常，否则，直接删除验证码
    if sms_code != redis_sms_code:
        raise ValidationError(message=message.sms_code_error, field_name="sms_code")

    redis.delete("sms_%s" % old_mobile)

    user.mobile = new_mobile
    db.session.commit()

    return {
        "errno": status.CODE_OK,
        "errmsg": message.ok,
        "mobile": new_mobile
    }


@jsonrpc.method("Recharge.create")
@jwt_required  # 验证jwt
def create_recharge(money=10):
    """创建充值订单"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if user is None:
        return {
            "errno": status.CODE_NO_USER,
            "errmsg": message.user_not_exists,
        }
    order_number = datetime.now().strftime("%y%m%d%H%M%S") + "%08d" % user.id + "%04d" % random.randint(0, 9999)

    print(order_number)

    recharge = Recharge(
        status=False,
        out_trade_number=order_number,
        name="账号充值-%s元" % money,
        user_id=user.id,
        money=money
    )
    db.session.add(recharge)
    db.session.commit()
    # 创建支付宝sdk对象
    app_private_key_string = open(
        os.path.join(current_app.BASE_DIR, "application/apps/users/keys/app_private_key.pem")).read()
    alipay_public_key_string = open(
        os.path.join(current_app.BASE_DIR, "application/apps/users/keys/app_public_key.pem")).read()

    alipay = AliPay(
        appid=current_app.config.get("ALIPAY_APP_ID"),
        app_notify_url=None,  # 默认回调url
        app_private_key_string=app_private_key_string,
        # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        alipay_public_key_string=alipay_public_key_string,
        sign_type=current_app.config.get("ALIPAY_SIGN_TYPE"),
        debug=False,  # 默认False
        config=AliPayConfig(timeout=15)  # 可选, 请求超时时间
    )

    order_string = alipay.api_alipay_trade_app_pay(
        out_trade_no=recharge.out_trade_number,  # 订单号
        total_amount=float(recharge.money),  # 订单金额
        subject=recharge.name,  # 订单标题
        notify_url=current_app.config.get("ALIPAY_NOTIFY_URL")  # 服务端的地址，自定义一个视图函数给alipay
    )

    return {
        "errno": status.CODE_OK,
        "errmsg": message.ok,
        "sandbox": current_app.config.get("ALIPAY_SANDBOX"),
        "order_string": order_string,
        "order_number": recharge.out_trade_number,
    }


def notify_response():
    """支付宝支付结果异步通知处理"""
    data = request.form.to_dict()
    # sign 不能参与签名验证
    signature = data.pop("sign")

    app_private_key_string = open(
        os.path.join(current_app.BASE_DIR, "application/apps/users/keys/app_private_key.pem")).read()
    alipay_public_key_string = open(
        os.path.join(current_app.BASE_DIR, "application/apps/users/keys/app_public_key.pem")).read()

    alipay = AliPay(
        appid=current_app.config.get("ALIPAY_APP_ID"),
        app_notify_url=None,  # 默认回调url
        app_private_key_string=app_private_key_string,
        # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        alipay_public_key_string=alipay_public_key_string,
        sign_type=current_app.config.get("ALIPAY_SIGN_TYPE"),
        debug=False,  # 默认False
        config=AliPayConfig(timeout=15)  # 可选, 请求超时时间
    )

    # verify
    success = alipay.verify(data, signature)
    if success and data["trade_status"] in ("TRADE_SUCCESS", "TRADE_FINISHED"):
        """充值成功"""
        out_trade_number = data["out_trade_no"]
        recharge = Recharge.query.filter(Recharge.out_trade_number == out_trade_number).first()
        if recharge is None:
            return "fail"
        recharge.status = True
        user = User.query.get(recharge.user_id)
        if user is None:
            return "fail"
        user.money += recharge.money
        db.session.commit()
    return "success"  # 必须只能是success


@jsonrpc.method("Recharge.return")
@jwt_required  # 验证jwt
def return_recharge(out_trade_number):
    """同步通知处理"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if user is None:
        return {
            "errno": status.CODE_NO_USER,
            "errmsg": message.user_not_exists,
        }

    recharge = Recharge.query.filter(Recharge.out_trade_number == out_trade_number).first()
    if recharge is None:
        return {
            "errno": status.CODE_RECHARGE_ERROR,
            "errmsg": message.recharge_not_exists,
        }

    recharge.status = True
    if user.money == None:
        user.money = 0.00
        db.session.commit()

    user.money += recharge.money

    db.session.commit()
    return {
        "errno": status.CODE_OK,
        "errmsg": message.ok,
        "money": float("%.2f" % user.money),
    }


def check_recharge():
    """可以使用查询订单借口保证支付结果同步处理的安全性"""
    # out_trade_numbe = "201229102634000000520662"
    # app_private_key_string = open(os.path.join(current_app.BASE_DIR, "application/apps/users/keys/app_private_key.pem")).read()
    # alipay_public_key_string = open(os.path.join(current_app.BASE_DIR, "application/apps/users/keys/app_public_key.pem")).read()
    #
    # alipay = AliPay(
    #     appid= current_app.config.get("ALIPAY_APP_ID"),
    #     app_notify_url=None,  # 默认回调url
    #     app_private_key_string=app_private_key_string,
    #     # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
    #     alipay_public_key_string=alipay_public_key_string,
    #     sign_type=current_app.config.get("ALIPAY_SIGN_TYPE"),
    #     debug = False,  # 默认False
    #     config = AliPayConfig(timeout=15)  # 可选, 请求超时时间
    # )
    # result = alipay.api_alipay_fund_trans_order_query(
    #     order_id=out_trade_numbe
    # )
    # print(result)
    # return result

    """
    path("/alipay/check", views.check_recharge),
    """

    return ""

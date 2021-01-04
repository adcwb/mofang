from application import socketio
from flask import request
from application.apps.users.models import User
from flask_socketio import join_room, leave_room
from application import mongo
from .models import Goods, Setting, db
from application.utils.language.status import APIStatus as status
from application.utils.language.message import ErrorMessage as errmsg


# 建立socket通信
# @socketio.on("connect", namespace="/mofang")
# def user_connect():
#     """用户连接"""
#     print("用户%s连接过来了!" % request.sid)
#     # 主动响应数据给客户端
#     socketio.emit("server_response","hello",namespace="/mofang")

# 断开socket通信
@socketio.on("disconnect", namespace="/mofang")
def user_disconnect():
    print("用户%s退出了种植园" % request.sid)


@socketio.on("login", namespace="/mofang")
def user_login(data):
    # 分配房间
    room = data["uid"]
    join_room(room)
    # 保存当前用户和sid的绑定关系
    # 判断当前用户是否在mongo中有记录
    query = {
        "_id": data["uid"]
    }
    ret = mongo.db.user_info_list.find_one(query)
    if ret:
        mongo.db.user_info_list.update_one(query, {"$set": {"sid": request.sid}})
    else:
        mongo.db.user_info_list.insert_one({
            "_id": data["uid"],
            "sid": request.sid,
        })

    # 返回种植园的相关配置参数
    orchard_settings = {}
    setting_list = Setting.query.filter(Setting.is_deleted == False, Setting.status == True).all()
    """
    现在的格式：
        [<Setting package_number_base>, <Setting package_number_max>, <Setting package_unlock_price_1>]
    需要返回的格式：
        {
            package_number_base:4,
            package_number_max: 32,
            ...
        }
    """
    for item in setting_list:
        orchard_settings[item.name] = item.value

    # 返回当前用户相关的配置参数
    user_settings = {}
    # 从mongo中查找用户信息，判断用户是否激活了背包格子
    dict = mongo.db.user_info_list.find_one({"sid": request.sid})
    # 背包格子
    if dict.get("package_number") is None:
        user_settings["package_number"] = orchard_settings.get("package_number_base", 4)
        mongo.db.user_info_list.update_one({"sid": request.sid},
                                           {"$set": {"package_number": user_settings["package_number"]}})
    else:
        user_settings["package_number"] = dict.get("package_number")

    socketio.emit("login_response", {
        "errno": status.CODE_OK,
        "errmsg": errmsg.ok,
        "orchard_settings": orchard_settings,
        "user_settings": user_settings
    }, namespace="/mofang", room=room)


@socketio.on("user_buy_prop", namespace="/mofang")
def user_buy_prop(data):
    """用户购买道具"""
    room = request.sid
    # 从mongo中获取当前用户信息
    user_info = mongo.db.user_info_list.find_one({"sid": request.sid})
    user = User.query.get(user_info.get("_id"))
    if user is None:
        socketio.emit("user_buy_prop_response", {"errno": status.CODE_NO_USER, "errmsg": errmsg.user_not_exists},
                      namespace="/mofang", room=room)
        return

    # 判断背包物品存储是否达到上限
    use_package_number = int(user_info.get("use_package_number", 0))  # 当前诗经使用的格子数量
    package_number = int(user_info.get("package_number", 0))  # 当前用户已经解锁的格子数量
    # 本次购买道具需要使用的格子数量
    setting = Setting.query.filter(Setting.name == "td_prop_max").first()
    if setting is None:
        td_prop_max = 10
    else:
        td_prop_max = int(setting.value)

    # 计算购买道具以后需要额外占用的格子数量
    if ("prop_%s" % data["pid"]) in user_info.get("prop_list", {}):
        """曾经购买过当前道具"""
        prop_num = int(user_info.get("prop_list")["prop_%s" % data["pid"]])  # 购买前的道具数量
        new_prop_num = prop_num + int(data["num"])  # 如果成功购买道具以后的数量
        old_td_num = prop_num // td_prop_max
        if prop_num % td_prop_max > 0:
            old_td_num += 1
        new_td_num = new_prop_num // td_prop_max
        if new_prop_num % td_prop_max > 0:
            new_td_num += 1
        td_num = new_td_num - old_td_num
    else:
        """新增购买的道具"""
        # 计算本次购买道具需要占用的格子数量

        if int(data["num"]) > td_prop_max:
            """需要多个格子"""
            td_num = int(data["num"]) // td_prop_max
            if int(data["num"]) % td_prop_max > 0:
                td_num += 1
        else:
            """需要一个格子"""
            td_num = 1

    if use_package_number + td_num > package_number:
        """超出存储上限"""
        socketio.emit("user_buy_prop_response", {"errno": status.CODE_NO_PACKAGE, "errmsg": errmsg.no_package},
                      namespace="/mofang", room=room)
        return

    # 从mysql中获取商品价格
    prop = Goods.query.get(data["pid"])
    if user.money > 0:  # 当前商品需要通过RMB购买
        if float(user.money) < float(prop.price) * int(data["num"]):
            socketio.emit("user_buy_prop_response", {"errno": status.CODE_NO_MONEY, "errmsg": errmsg.money_no_enough},
                          namespace="/mofang", room=room)
            return
    else:
        """当前通过果子进行购买"""
        if int(user.credit) < int(prop.credit) * int(data["num"]):
            socketio.emit("user_buy_prop_response", {"errno": status.CODE_NO_CREDIT, "errmsg": errmsg.credit_no_enough},
                          namespace="/mofang", room=room)
            return

    # 从mongo中获取用户列表信息，提取购买的商品数量进行累加和余额
    query = {"sid": request.sid}
    if user_info.get("prop_list") is None:
        """此前没有购买任何道具"""
        message = {"$set": {"prop_list": {"prop_%s" % prop.id: int(data["num"])}}}
        mongo.db.user_info_list.update_one(query, message)
    else:
        """此前有购买了道具"""
        prop_list = user_info.get("prop_list")  # 道具列表
        if ("prop_%s" % prop.id) in prop_list:
            """如果再次同一款道具"""
            prop_list[("prop_%s" % prop.id)] = prop_list[("prop_%s" % prop.id)] + int(data["num"])
        else:
            """此前没有购买过这种道具"""
            prop_list[("prop_%s" % prop.id)] = int(data["num"])

        mongo.db.user_info_list.update_one(query, {"$set": {"prop_list": prop_list}})

    # 扣除余额或果子
    if prop.price > 0:
        user.money = float(user.money) - float(prop.price) * int(data["num"])
    else:
        user.credit = int(user.credit) - int(prop.credit) * int(data["num"])

    db.session.commit()

    # 返回购买成功的信息
    socketio.emit("user_buy_prop_response", {"errno": status.CODE_OK, "errmsg": errmsg.ok}, namespace="/mofang",
                  room=room)
    # 返回最新的用户道具列表
    user_prop()


@socketio.on("user_prop", namespace="/mofang")
def user_prop():
    """用户道具"""
    userinfo = mongo.db.user_info_list.find_one({"sid": request.sid})
    prop_list = userinfo.get("prop_list", {})
    prop_id_list = []
    for prop_str, num in prop_list.items():
        pid = int(prop_str[5:])
        prop_id_list.append(pid)

    data = []
    prop_list_data = Goods.query.filter(Goods.id.in_(prop_id_list)).all()
    setting = Setting.query.filter(Setting.name == "td_prop_max").first()
    if setting is None:
        td_prop_max = 10
    else:
        td_prop_max = int(setting.value)

    for prop_data in prop_list_data:
        num = int(prop_list[("prop_%s" % prop_data.id)])
        if td_prop_max > num:
            data.append({
                "num": num,
                "image": prop_data.image,
                "pid": prop_data.id
            })
        else:
            padding_time = num // td_prop_max
            padding_last = num % td_prop_max
            arr = [{
                "num": td_prop_max,
                "image": prop_data.image,
                "pid": prop_data.id
            }] * padding_time
            if padding_last != 0:
                arr.append({
                    "num": padding_last,
                    "image": prop_data.image,
                    "pid": prop_data.id
                })
            data = data + arr
    mongo.db.user_info_list.update_one({"sid": request.sid}, {"$set": {"use_package_number": len(data)}})
    room = request.sid
    socketio.emit("user_prop_response", {
        "errno": status.CODE_OK,
        "errmsg": errmsg.ok,
        "data": data,
    }, namespace="/mofang",
                  room=room)


@socketio.on("unlock_package", namespace="/mofang")
def unlock_package():
    """解锁背包"""
    # 从mongo获取当前用户解锁的格子数量
    user_info = mongo.db.user_info_list.find_one({"sid": request.sid})
    user = User.query.get(user_info.get("_id"))
    if user is None:
        socketio.emit("unlock_package_response", {"errno": status.CODE_NO_USER, "errmsg": errmsg.user_not_exists},
                      namespace="/mofang", room=room)
        return

    package_number = int(user_info.get("package_number"))
    num = 7 - (32 - package_number) // 4  # 没有解锁的格子

    # 从数据库中获取解锁背包的价格
    setting = Setting.query.filter(Setting.name == "package_unlock_price_%s" % num).first()
    if setting is None:
        unlock_price = 0
    else:
        unlock_price = int(setting.value)

    # 判断是否有足够的积分或者价格
    room = request.sid
    if user.money < unlock_price:
        socketio.emit("unlock_package_response", {"errno": status.CODE_NO_MONEY, "errmsg": errmsg.money_no_enough},
                      namespace="/mofang", room=room)
        return

    # 解锁成功
    user.money = float(user.money) - float(unlock_price)
    db.session.commit()

    # mongo中调整数量
    mongo.db.user_info_list.update_one({"sid": request.sid}, {"$set": {"package_number": package_number + 1}})
    # 返回解锁的结果
    socketio.emit("unlock_package_response", {
        "errno": status.CODE_OK,
        "errmsg": errmsg.ok},
                  namespace="/mofang", room=room)


import math
from application import redis


@socketio.on("pet_show", namespace="/mofang")
def pet_show():
    """显示宠物"""
    room = request.sid
    user_info = mongo.db.user_info_list.find_one({"sid": request.sid})
    user = User.query.get(user_info.get("_id"))
    if user is None:
        socketio.emit("pet_show_response", {"errno": status.CODE_NO_USER, "errmsg": errmsg.user_not_exists},
                      namespace="/mofang", room=room)
        return

    # 获取宠物列表
    pet_list = user_info.get("pet_list", [])

    """
    pet_list: [
      { 
         "pid":11,
         "image":"pet.png",
         "hp":100%,
         "created_time":xxxx-xx-xx xx:xx:xx,
         "skill":"70%",
         "has_time":30天
      },
    ]
    """
    # 从redis中提取当前宠物的饱食度和有效期
    for key, pet in enumerate(pet_list):
        pet["hp"] = math.ceil(redis.ttl("pet_%s_%s_hp" % (user.id, key + 1)) / 86400 * 100)
        pet["has_time"] = redis.ttl("pet_%s_%s_expire" % (user.id, key + 1))

    pet_number = user_info.get("pet_number", 1)
    socketio.emit(
        "pet_show_response",
        {
            "errno": status.CODE_OK,
            "errmsg": errmsg.ok,
            "pet_list": pet_list,
            "pet_number": pet_number,
        },
        namespace="/mofang",
        room=room
    )


from datetime import datetime


@socketio.on("use_prop", namespace="/mofang")
def use_prop(pid):
    """使用宠物"""
    # 1. 判断当前的宠物数量
    room = request.sid
    user_info = mongo.db.user_info_list.find_one({"sid": request.sid})
    user = User.query.get(user_info.get("_id"))
    if user is None:
        socketio.emit("pet_use_response", {"errno": status.CODE_NO_USER, "errmsg": errmsg.user_not_exists},
                      namespace="/mofang", room=room)
        return

    # 获取宠物列表
    pet_list = user_info.get("pet_list", [])
    if len(pet_list) > 1:
        socketio.emit("pet_use_response", {"errno": status.CODE_NO_EMPTY, "errmsg": errmsg.pet_not_empty},
                      namespace="/mofang", room=room)
        return

    # 2. 是否有空余的宠物栏位
    pet_number = user_info.get("pet_number", 1)
    if pet_number <= len(pet_list):
        socketio.emit("pet_use_response", {"errno": status.CODE_NO_EMPTY, "errmsg": errmsg.pet_not_empty},
                      namespace="/mofang", room=room)
        return

    # 3. 初始化当前宠物信息
    pet = Goods.query.get(pid)
    if pet is None:
        socketio.emit("pet_use_response", {"errno": status.CODE_NO_SUCH_PET, "errmsg": errmsg.not_such_pet},
                      namespace="/mofang", room=room)
        return

    # 获取有效期和防御值
    exp_data = Setting.query.filter(Setting.name == "pet_expire_%s" % pid).first()
    ski_data = Setting.query.filter(Setting.name == "pet_skill_%s" % pid).first()

    if exp_data is None:
        # 默认7天有效期
        expire = 7
    else:
        expire = exp_data.value

    if ski_data is None:
        skill = 10
    else:
        skill = ski_data.value

    # 在redis中设置当前宠物的饱食度
    pipe = redis.pipeline()
    pipe.multi()
    pipe.setex("pet_%s_%s_hp" % (user.id, len(pet_list) + 1), 24 * 60 * 60, "_")
    pipe.setex("pet_%s_%s_expire" % (user.id, len(pet_list) + 1), int(expire) * 24 * 60 * 60, "_")
    pipe.execute()

    # 基本保存到mongo
    mongo.db.user_info_list.update_one({"sid": request.sid}, {"$push": {"pet_list": {
        "pid": pid,
        "image": pet.image,
        "created_time": int(datetime.now().timestamp()),
        "skill": skill,
    }}})

    """
    db.user_info_list.updateOne({"_id":"52"},{"$push":{"pet_list":{
             "pid": 2,
             "image": "pet1.png",
             "created_time": 1609727155,
             "skill": 30,
          }}})
    """

    # 扣除背包中的道具数量
    prop_list = user_info.get("prop_list", {})
    for key, value in prop_list.items():
        if key == ("prop_%s" % pid):
            if int(value) > 1:
                prop_list[key] = int(value) - 1
            else:
                prop_list.pop(key)
            break

    mongo.db.user_info_list.update_one({"sid": room}, {"$set": {"prop_list": prop_list}})
    user_prop()
    pet_show()

    socketio.emit("pet_use_response", {"errno": status.CODE_OK, "errmsg": errmsg.ok},
                  namespace="/mofang", room=room)

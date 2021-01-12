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
    user_dict = mongo.db.user_info_list.find_one({"sid": request.sid})
    # 背包格子
    if user_dict.get("package_number") is None:
        user_settings["package_number"] = orchard_settings.get("package_number_base", 4)
        mongo.db.user_info_list.update_one({"sid": request.sid},
                                           {"$set": {"package_number": user_settings["package_number"]}})
    else:
        user_settings["package_number"] = user_dict.get("package_number")

    """种植园植物信息"""
    # 总树桩数量
    setting = Setting.query.filter(Setting.name == "user_total_tree").first()
    if setting is None:
        tree_total = 9
    else:
        tree_total = int(setting.value)

    # 用户已经激活的树桩
    setting = Setting.query.filter(Setting.name == "user_active_tree").first()
    if setting is None:
        user_tree_number = 3
    else:
        user_tree_number = int(setting.value)
    user_tree_number = user_dict.get("user_tree_number", user_tree_number)

    # 种植的植物列表
    user_tree_list = user_dict.get("user_tree_list", [])
    key = 0
    for tree_item in user_tree_list:
        tree_item["status"] = "tree_status_%s" % int(tree_item["status"])  # 植物状态
        tree_item["water_time"] = redis.ttl("user_tree_water_%s_%s" % (data["uid"], key))
        tree_item["growup_time"] = redis.ttl("user_tree_growup_%s_%s" % (data["uid"], key))
        key += 1
    # 植物状态信息
    status_list = [
        "tree_status_0",
        "tree_status_1",
        "tree_status_2",
        "tree_status_3",
        "tree_status_4",
    ]
    setting_list = Setting.query.filter(Setting.name.in_(status_list)).all()
    tree_status = {}
    for item in setting_list:
        tree_status[item.name] = item.value

    """显示植物相关道具"""
    # 获取背包中的化肥和宠物粮
    fertilizer_num, pet_food_num = get_package_prop_list(user_dict)
    # 获取剪刀和浇水
    # 只有植物处于成长期才会允许裁剪
    # 只有植物处于幼苗期才会允许浇水
    waters = 0
    shears = 0
    user_tree_list = user_dict.get("user_tree_list", [])
    if len(user_tree_list) > 0:
        key = 0
        for tree in user_tree_list:
            if (tree["status"] == "tree_status_%s" % 2) and int(tree.get("waters", 0)) == 0:
                """处于幼苗期"""
                # 判断只有种植指定时间以后的幼苗才可以浇水
                interval_time = redis.ttl("user_tree_water_%s_%s" % (user_dict.get("_id"), key))
                if interval_time == -2:
                    waters += 1

            elif (tree["status"] == "tree_status_%s" % 3) and int(tree.get("shears", 0)) == 0:
                """处于成长期"""
                interval_time = redis.ttl("user_tree_shears_%s_%s" % (user_dict.get("_id"), key))
                if interval_time == -2:
                    shears += 1
            key += 1

    message = {
        "errno": status.CODE_OK,
        "errmsg": errmsg.ok,
        "orchard_settings": orchard_settings,
        "user_settings": user_settings,
        "tree_total": tree_total,
        "user_tree_number": user_tree_number,
        "user_tree_list": user_tree_list,
        "fertilizer_num": fertilizer_num,
        "pet_food_num": pet_food_num,
        "tree_status": tree_status,
        "waters": waters,
        "shears": shears,
    }
    socketio.emit("login_response", message, namespace="/mofang", room=room)


def get_package_prop_list(user_dict):
    fertilizer_num = 0
    pet_food_num = 0
    prop_list = user_dict.get("prop_list", {})
    for prop_item, num in prop_list.items():
        pid = prop_item.split("_")[-1]
        num = int(num)
        prop_obj = Goods.query.get(pid)
        if prop_obj.prop_type == 2:
            # 提取化肥
            fertilizer_num += num
        elif prop_obj.prop_type == 3:
            # 提取宠物粮
            pet_food_num += num

    return fertilizer_num, pet_food_num


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
                "pid": prop_data.id,
                "pty": prop_data.prop_type,
            })
        else:
            padding_time = num // td_prop_max
            padding_last = num % td_prop_max
            arr = [{
                "num": td_prop_max,
                "image": prop_data.image,
                "pid": prop_data.id,
                "pty": prop_data.prop_type,
            }] * padding_time
            if padding_last != 0:
                arr.append({
                    "num": padding_last,
                    "image": prop_data.image,
                    "pid": prop_data.id,
                    "pty": prop_data.prop_type,
                })
            data = data + arr
    mongo.db.user_info_list.update_one({"sid": request.sid}, {"$set": {"use_package_number": len(data)}})
    room = request.sid
    fertilizer_num, pet_food_num = get_package_prop_list(userinfo)
    socketio.emit("user_prop_response", {
        "errno": status.CODE_OK,
        "errmsg": errmsg.ok,
        "data": data,
        "fertilizer_num": fertilizer_num,
        "pet_food_num": pet_food_num,
    }, namespace="/mofang",
                  room=room)


@socketio.on("unlock_package", namespace="/mofang")
def unlock_package():
    """解锁背包"""
    # 从mongo获取当前用户解锁的格子数量
    room = request.sid
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
    # 初始化宠物的生命周期
    pet_hp_max = 10000
    for key, pet in enumerate(pet_list):
        setting = Setting.query.filter(Setting.name == "pet_hp_max_%s" % pet["pid"]).first()
        if setting is None:
            pet_hp_max = 7200
        else:
            pet_hp_max = int(setting.value)
        pet["hp"] = math.ceil(redis.ttl("pet_%s_%s_hp" % (user.id, key + 1)) / pet_hp_max * 100)
        pet["has_time"] = redis.ttl("pet_%s_%s_expire" % (user.id, key + 1))
        pet["hp_time"] = redis.ttl("pet_%s_%s_hp" % (user.id, key + 1))
        pet["pet_hp_max"] = pet_hp_max
        # 在饱食度低于0时，给当前宠物进行标记
        if pet["hp"] <= 0:
            pet["is_die"] = 1
            redis.delete("pet_%s_%s_expire" % (user.id, key + 1))

    mongo.db.user_info_list.update_one({"sid": room}, {"$set": {"pet_list": pet_list}})

    pet_number = user_info.get("pet_number", 1)
    print(pet_list)
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
def use_prop(data):
    """使用道具"""
    pid = data.get("pid")
    pet_key = data.get("pet_key", 0)
    room = request.sid
    # 获取mongo中的用户信息
    user_info = mongo.db.user_info_list.find_one({"sid": request.sid})
    # 获取mysql中的用户信息
    user = User.query.get(user_info.get("_id"))
    if user is None:
        socketio.emit("pet_use_response", {"errno": status.CODE_NO_USER, "errmsg": errmsg.user_not_exists},
                      namespace="/mofang", room=room)
        return

    # 获取道具
    prop_data = Goods.query.get(pid)
    if prop_data is None:
        socketio.emit("pet_use_response", {"errno": status.CODE_NO_SUCH_PROP, "errmsg": errmsg.not_such_prop},
                      namespace="/mofang", room=room)
        return

    if int(prop_data.prop_type) == 0:
        """使用植物道具"""
        # 1. 判断当前的植物数量是否有空余
        tree_list = user_info.get("user_tree_list", [])

        # 当前用户最多可种植的数量
        setting = Setting.query.filter(Setting.name == "user_active_tree").first()
        if setting is None:
            user_tree_number = 3
        else:
            user_tree_number = int(setting.value)
        user_tree_number = user_info.get("user_tree_number", user_tree_number)

        if len(tree_list) >= user_tree_number:
            socketio.emit("prop_use_response", {"errno": status.CODE_NO_EMPTY, "errmsg": errmsg.prop_not_empty},
                          namespace="/mofang", room=room)
            return

        # 使用道具
        mongo.db.user_info_list.update_one({"sid": room}, {"$push": {"user_tree_list":
            {  # 植物状态
                "time": int(datetime.now().timestamp()),  # 种植时间
                "status": 2,  # 植物状态，2表示幼苗状态
                "allow_water": False,  # 是否允许浇水
                "waters": 0,  # 浇水次数
                "shears": 0,  # 使用剪刀次数
            }
        }})

        # 从种下去到浇水的时间
        pipe = redis.pipeline()
        pipe.multi()
        setting = Setting.query.filter(Setting.name == "tree_water_time").first()
        if setting is None:
            tree_water_time = 3600
        else:
            tree_water_time = int(setting.value)
        # 必须等时间到了才可以浇水
        pipe.setex("user_tree_water_%s_%s" % (user.id, len(tree_list)), int(tree_water_time), "_")
        # 必须等时间到了才可以到成长期
        setting = Setting.query.filter(Setting.name == "tree_growup_time").first()
        if setting is None:
            tree_growup_time = 3600
        else:
            tree_growup_time = int(setting.value)
        pipe.setex("user_tree_growup_%s_%s" % (user.id, len(tree_list)), tree_growup_time, "_")
        pipe.execute()

        # 设置定时任务进行浇水
        redis.append("tree_list_water", "%s_%s," % (user.id, len(tree_list)))
        user_login({"uid": user.id})

    if int(prop_data.prop_type) == 1:
        """使用宠物道具"""
        # 1. 判断当前的宠物数量
        # 获取宠物列表
        pet_list = user_info.get("pet_list", [])
        if len(pet_list) > 1 and pet_list[0]['is_die'] == 0 and pet_list[1]['is_die'] == 0:
            socketio.emit("pet_use_response", {"errno": status.CODE_NO_EMPTY, "errmsg": errmsg.pet_not_empty},
                          namespace="/mofang", room=room)
            return

        # 2. 是否有空余的宠物栏位
        pet_number = user_info.get("pet_number", 1)
        length = len(pet_list)

        if length == 2:
            live_leng = 0
            if pet_list[0]['is_die'] == 0:
                live_leng += 1
            if pet_list[1]['is_die'] == 0:
                live_leng += 1
        elif length == 1 and pet_list[0]['is_die'] == 0:
            live_leng = 1
        else:
            live_leng = 0
        if live_leng >= pet_number:
            socketio.emit("pet_use_response", {"errno": status.CODE_NO_EMPTY, "errmsg": errmsg.pet_not_empty},
                          namespace="/mofang", room=room)
            return

        # 3. 初始化当前宠物信息
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
        setting = Setting.query.filter(Setting.name == ("pet_hp_max_%s" % pid)).first()
        if setting is None:
            pet_hp_max = 7200
        else:
            pet_hp_max = int(setting.value)

        # 基本保存到mongo
        # 判断是否有挂了的宠物在列表中
        pet_data = {
            "pid": pid,
            "image": prop_data.image,
            "created_time": int(datetime.now().timestamp()),
            "skill": skill,
            "is_die": 0,
        }

        # 如果第一个宠物是挂了的
        if len(pet_list) == 0:
            mongo.db.user_info_list.update_one({"sid": room}, {"$set": {"pet_list": [pet_data]}})

            pipe.setex("pet_%s_%s_hp" % (user.id, 1), pet_hp_max, "_")
            pipe.setex("pet_%s_%s_expire" % (user.id, 1), int(expire) * 24 * 60 * 60, "_")
        elif len(pet_list) == 1 and int(pet_list[0]["is_die"]) == 1:
            """只有一个挂了的宠物"""
            mongo.db.user_info_list.update_one({"sid": room}, {"$set": {"pet_list": [pet_data]}})

            pipe.setex("pet_%s_%s_hp" % (user.id, 1), pet_hp_max, "_")
            pipe.setex("pet_%s_%s_expire" % (user.id, 1), int(expire) * 24 * 60 * 60, "_")

        elif len(pet_list) == 1 and int(pet_list[0]["is_die"]) == 0:
            """只有一个活着的宠物"""
            mongo.db.user_info_list.update_one({"sid": room}, {"$push": {"pet_list": pet_data}})
            pipe.setex("pet_%s_%s_hp" % (user.id, 2), pet_hp_max, "_")
            pipe.setex("pet_%s_%s_expire" % (user.id, 2), int(expire) * 24 * 60 * 60, "_")
        elif len(pet_list) == 2 and int(pet_list[0]["is_die"]) == 1:
            """有2个宠物，但是第1个挂了"""
            pet_list[0] = pet_data
            mongo.db.user_info_list.update_one({"sid": room}, {"$set": {"pet_list": pet_list}})
            pipe.setex("pet_%s_%s_hp" % (user.id, 1), pet_hp_max, "_")
            pipe.setex("pet_%s_%s_expire" % (user.id, 1), int(expire) * 24 * 60 * 60, "_")
        elif len(pet_list) == 2 and int(pet_list[1]["is_die"]) == 1:
            """有2个宠物，但是第2个挂了"""
            pet_list[1] = pet_data
            pipe.setex("pet_%s_%s_hp" % (user.id, 2), pet_hp_max, "_")
            pipe.setex("pet_%s_%s_expire" % (user.id, 2), int(expire) * 24 * 60 * 60, "_")
            mongo.db.user_info_list.update_one({"sid": room}, {"$set": {"pet_list": pet_list}})

        pipe.execute()
        pet_show()

    if int(prop_data.prop_type) == 3:
        """宠物喂食"""

        pet_list = user_info.get("pet_list")
        if len(pet_list) < 1:
            socketio.emit("pet_use_response", {"errno": status.CODE_NO_PET, "errmsg": errmsg.not_pet},
                          namespace="/mofang", room=room)
            return

        current_hp_time = redis.ttl("pet_%s_%s_hp" % (user.id, pet_key + 1))
        setting = Setting.query.filter(Setting.name == ("pet_hp_max_%s" % (pet_list[pet_key]["pid"]))).first()
        if setting is None:
            pet_hp_max = 7200
        else:
            pet_hp_max = int(setting.value)

        current_pet_hp = math.ceil(current_hp_time / pet_hp_max * 100)

        if current_pet_hp > 90:
            """饱食度高于90%无法喂养"""
            socketio.emit("pet_use_response", {"errno": status.CODE_NO_FEED, "errmsg": errmsg.no_feed},
                          namespace="/mofang", room=room)
            return

        if current_pet_hp <= 0:
            socketio.emit("pet_use_response", {"errno": status.CODE_NO_PET, "errmsg": errmsg.not_pet},
                          namespace="/mofang", room=room)
            return
        setting = Setting.query.filter(Setting.name == "pet_feed_number").first()
        if setting is None:
            pet_feed_number = 0.1
        else:
            pet_feed_number = float(setting.value)
        prop_time = pet_hp_max * pet_feed_number
        time = int(current_hp_time + prop_time)

        redis.expire("pet_%s_%s_hp" % (user.id, pet_key + 1), time)
        socketio.emit("pet_feed_response",
                      {"errno": status.CODE_OK, "errmsg": errmsg.ok, "pet_key": pet_key, "hp_time": time},
                      namespace="/mofang", room=room)
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

    socketio.emit("prop_use_response", {"errno": status.CODE_OK, "errmsg": errmsg.ok},
                  namespace="/mofang", room=room)


@socketio.on("active_tree", namespace="/mofang")
def active_tree():
    """激活树桩"""
    room = request.sid
    # 获取mongo中的用户信息
    user_info = mongo.db.user_info_list.find_one({"sid": request.sid})
    # 获取mysql中的用户信息
    user = User.query.get(user_info.get("_id"))
    if user is None:
        socketio.emit("active_tree_response", {"errno": status.CODE_NO_USER, "errmsg": errmsg.user_not_exists},
                      namespace="/mofang", room=room)
        return

    # 判断树桩是否达到上限
    tree_number_data = Setting.query.filter(Setting.name == "user_active_tree").first()
    total_tree_data = Setting.query.filter(Setting.name == "user_total_tree").first()
    if tree_number_data is None:
        tree_number = 1
    else:
        tree_number = tree_number_data.value

    if total_tree_data is None:
        total_tree = 9
    else:
        total_tree = int(total_tree_data.value)

    user_tree_number = int(user_info.get("user_tree_number", tree_number))
    if user_tree_number >= total_tree:
        socketio.emit("active_tree_response", {"errno": status.CODE_NO_EMPTY, "errmsg": errmsg.prop_not_empty},
                      namespace="/mofang", room=room)
        return

    # 扣除激活的果子数量
    ret = Setting.query.filter(Setting.name == "active_tree_price").first()
    if ret is None:
        active_tree_price = 100 * user_tree_number
    else:
        active_tree_price = int(ret.value) * user_tree_number

    if active_tree_price > int(user.credit):
        socketio.emit("active_tree_response", {"errno": status.CODE_NO_CREDIT, "errmsg": errmsg.credit_no_enough},
                      namespace="/mofang", room=room)
        return

    user.credit = int(user.credit) - active_tree_price
    db.session.commit()

    mongo.db.user_info_list.update_one({"sid": room}, {"$set": {"user_tree_number": user_tree_number + 1}})

    socketio.emit("active_tree_response", {"errno": status.CODE_OK, "errmsg": errmsg.ok},
                  namespace="/mofang", room=room)
    return


@socketio.on("water_tree", namespace="/mofang")
def water_tree(key):
    """浇水"""
    room = request.sid
    # 获取mongo中的用户信息
    query = {"sid": request.sid}
    user_info = mongo.db.user_info_list.find_one(query)
    # 获取mysql中的用户信息
    user = User.query.get(user_info.get("_id"))
    if user is None:
        socketio.emit("water_tree_response", {"errno": status.CODE_NO_USER, "errmsg": errmsg.user_not_exists},
                      namespace="/mofang", room=room)
        return

    print("给%s的植物%s" % (user.id, key))
    user_tree_list = user_info.get("user_tree_list", [])
    try:
        tree_data = user_tree_list[key]
    except Exception as e:
        socketio.emit("water_tree_response", {"errno": status.CODE_NO_SUCH_TREE, "errmsg": errmsg.tree_not_exists},
                      namespace="/mofang", room=room)
        return

    if tree_data.get("allow_water", False) and int(tree_data.get("waters", 1)) == 0:
        """允许浇水"""
        tree_data["waters"] = 1
        # 如果种植物的种植时间达到成长期，则修改种植物的成长状态
        growup = redis.ttl("user_tree_growup_%s_%s" % (user.id, key))
        if growup == -2:
            tree_data["status"] = 3

    mongo.db.user_info_list.update_one(query, {"$set": {"user_tree_list": user_tree_list}})
    socketio.emit("water_tree_response", {"errno": status.CODE_OK, "errmsg": errmsg.ok},
                  namespace="/mofang", room=room)
    user_login({"uid": user.id})

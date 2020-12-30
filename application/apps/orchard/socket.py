from application import socketio
from flask import request
from application.apps.users.models import User
from flask_socketio import join_room, leave_room
from application import mongo
from .models import Goods
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
    # request.sid socketIO基于客户端生成的唯一会话ID
    print("用户%s退出了种植园" % request.sid)


@socketio.on("login", namespace="/mofang")
def user_login(data):
    # 分配房间
    print(">>>>>>>>>>>>>>>>>>>>>>>", data)
    room = data["uid"]  # 当前用户id
    join_room(room)
    # 保存当前用户和sid的绑定关系
    # 判断当前用户是否在mongo中有记录
    query = {
        "_id": data["uid"]
    }
    ret = mongo.db.user_info_list.find_one(query)
    # 判断当前用户是否在mongo中有记录，如果有，就更新，没有就插入
    if ret:
        mongo.db.user_info_list.update_one(query, {"$set": {"sid": request.sid}})
    else:
        mongo.db.user_info_list.insert_one({
            "_id": data["uid"],
            "sid": request.sid,
        })

    # 发送信息给客户端
    socketio.emit("login_response", {"errno": status.CODE_OK, "errmsg": errmsg.ok}, namespace="/mofang", room=room)


@socketio.on("user_buy_prop", namespace="/mofang")      # user_buy_prop 自定义事件
def user_buy_prop(data):
    """用户购买道具"""
    room = request.sid
    # print(request)      <Request 'http://192.168.20.5:5000/socket.io/?EIO=4&transport=websocket' [GET]>
    # print(data)     {'pid': 2, 'num': '1'}
    # 从mongo中获取当前用户信息
    user_info = mongo.db.user_info_list.find_one({"sid": request.sid})
    user = User.query.get(user_info.get("_id"))
    if user is None:
        socketio.emit("user_buy_prop_response", {"errno": status.CODE_NO_USER, "errmsg": errmsg.user_not_exists},
                      namespace="/mofang", room=room)
        return

    # 从mysql中获取商品价格
    prop = Goods.query.get(data["pid"])
    if float(user.money) < float(prop.price) * int(data["num"]):
        socketio.emit("user_buy_prop_response", {"errno": status.CODE_NO_MONEY, "errmsg": errmsg.money_no_enough},
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

    socketio.emit("user_buy_prop_response", {"errno": status.CODE_OK, "errmsg": errmsg.ok}, namespace="/mofang",
                  room=room)

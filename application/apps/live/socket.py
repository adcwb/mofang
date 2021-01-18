from application import socketio
from flask import request
from flask_socketio import join_room, leave_room
from application import mongo
from status import APIStatus as status
from message import ErrorMessage as errmsg
from application.apps.users.models import User
from datetime import datetime
from flask import current_app
from application import redis


def user_log(room, uid, content):
    query = {
        "_id": room
    }
    user = User.query.get(uid)
    if user is None:
        message = {
            "errno": status.CODE_NO_USER,
            "errmsg": errmsg.user_not_exists,
        }
        socketio.emit("login_response", message, namespace="/mofang", room=room)
        return

    name = user.nickname if user.nickname else user.name
    message = {
        "uid": user.id,
        "sid": request.sid,
        "user": name,
        "avatar": user.avatar if user.avatar else current_app.config["DEFAULT_AVATAR"],
        'created_time': int(datetime.now().timestamp()),
    }
    if "%s" in content:
        message["log"] = content % name
    else:
        message["message"] = content

    chat_list = mongo.db.user_chat_list.find_one(query)
    if not chat_list:
        mongo.db.user_chat_list.insert_one(query, {"stream_name": room})

    key = "%s_%s" % (room, request.sid)
    print(key)
    redis.set(key, user.id)
    mongo.db.user_chat_list.update_one(query, {"$push": {"message_list": message}})
    return message


@socketio.on("disconnect", namespace="/mofang")
def user_disconnect():
    """退出房间"""
    keys_list = redis.keys("*_%s" % request.sid)
    if len(keys_list) > 0:
        room_dict = keys_list[-1]
        uid = redis.get(room_dict).decode()
        room = "_".join(room_dict.decode().split("_")[:2])
        redis.delete(keys_list[-1].decode())
        message = user_log(room, uid, "%s退出了房间")
        socketio.emit("login_response", message, namespace="/mofang", room=room)
        leave_room(room)
    else:
        print("用户%s退出了房间" % request.sid)


@socketio.on("login", namespace="/mofang")
def user_login(data):
    # 进入房间
    room = data["stream_name"]
    join_room(room)
    message = user_log(room, data["uid"], "%s进入了房间")
    socketio.emit("login_response", message, namespace="/mofang", room=room)


@socketio.on("message", namespace="/mofang")
def user_message(data):
    """用户发送文本信息"""
    print(data)
    room = data["stream_name"]
    message = user_log(room, data["uid"], data["message"])
    socketio.emit("login_response", message, namespace="/mofang", room=room)

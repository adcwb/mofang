from application import jsonrpc, db
from application.utils.language.message import ErrorMessage as message
from application.utils.language.status import APIStatus as status
from flask_jwt_extended import jwt_required, get_jwt_identity
from application.apps.users.models import User
from .models import LiveStream, LiveRoom
from .marshmallow import StreamInfoSchema
from flask import current_app
from datetime import datetime
import random


@jsonrpc.method("Live.stream")
@jwt_required  # 验证jwt
def live_stream(room_name, password):
    """创建直播流"""
    current_user_id = get_jwt_identity()  # get_jwt_identity 用于获取载荷中的数据
    user = User.query.get(current_user_id)
    if user is None:
        return {
            "errno": status.CODE_NO_USER,
            "errmsg": message.user_not_exists,
        }
    # 申请创建直播流
    stream = LiveStream.query.filter(LiveStream.user == user.id).first()
    if stream is None:
        stream_name = "room_%06d%s%06d" % (
            user.id, datetime.now().strftime("%Y%m%d%H%M%S"), random.randint(100, 999999))
        stream = LiveStream(
            name=stream_name,
            user=user.id,
            room_name=room_name,
            room_password=password
        )
        db.session.add(stream)
        db.session.commit()
    else:
        stream.room_name = room_name
        stream.room_password = password
        db.session.commit()

    # 进入房间
    room = LiveRoom.query.filter(LiveRoom.user == user.id, LiveRoom.stream_id == stream.id).first()
    if room is None:
        room = LiveRoom(
            stream_id=stream.id,
            user=user.id
        )
        db.session.add(room)
        db.session.commit()

    return {
        "errno": status.CODE_OK,
        "errmsg": message.ok,
        "data": {
            "stream_name": stream.name,
            "room_name": room_name,
            "room_owner": user.id,
            "room_id": "%04d" % stream.id,
        }
    }


@jsonrpc.method("Live.stream.list")
@jwt_required  # 验证jwt
def list_stream():
    """房间列表"""
    current_user_id = get_jwt_identity()  # get_jwt_identity 用于获取载荷中的数据
    user = User.query.get(current_user_id)
    if user is None:
        return {
            "errno": status.CODE_NO_USER,
            "errmsg": message.user_not_exists,
            "data": {

            }
        }

    stream_list = LiveStream.query.filter(LiveStream.status == True, LiveStream.is_deleted == False).all()
    sis = StreamInfoSchema()
    data_list = sis.dump(stream_list, many=True)

    # 使用requests发送get请求
    import requests
    stream_response = requests.get(current_app.config["SRS_HTTP_API"] + "streams/")
    client_response = requests.get(current_app.config["SRS_HTTP_API"] + "clients/")
    import re, json
    stream_text = re.sub(r'[^\{\}\/\,0-9a-zA-Z\"\'\:\[\]\._]', "", stream_response.text)
    client_text = re.sub(r'[^\{\}\/\,0-9a-zA-Z\"\:\[\]\._]', "", client_response.text)
    stream_dict = json.loads(stream_text)
    client_dict = json.loads(client_text)
    outline_list = []
    for data in data_list:
        data["status"] = False
        for stream in stream_dict["streams"]:
            if data["name"] == stream["name"]:
                data["status"] = stream["publish"]["active"]
                break
        data["clients_number"] = 0
        for client in client_dict["clients"]:
            if data["name"] == client["url"].split("/")[-1]:
                data["clients_number"] += 1
            if client["publish"] and "/live/" + data["name"] == client["url"]:
                data["user"]["ip"] = client["ip"]

        if data["status"] == False:
            outline_list.append(data)

    for item in outline_list:
        data_list.remove(item)
    data_list += outline_list
    return {
        "errno": status.CODE_OK,
        "errmsg": message.ok,
        "stream_list": data_list
    }

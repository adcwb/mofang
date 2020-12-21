from application import socketio
from flask import request

# 建立socket通信
@socketio.on("connect", namespace="/mofang")
def user_connect():
    # request.sid socketIO基于客户端生成的唯一会话ID
    print("用户%s连接过来了!" % request.sid)

# 断开socket通信
@socketio.on("disconnect", namespace="/mofang")
def user_disconnect():
    print("用户%s退出了种植园" % request.sid )

# 未定义事件通信，客户端没有指定事件名称
@socketio.on("message",namespace="/mofang")
def user_message(data):
    print("接收到来自%s发送的数据:" % request.sid)
    print(data)
    print(data["uid"])
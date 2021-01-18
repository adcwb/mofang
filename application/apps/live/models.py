from application.utils.models import BaseModel, db


class LiveStream(BaseModel):
    """直播流管理"""
    __tablename__ = "mf_live_stream"
    name = db.Column(db.String(255), unique=True, comment="流名称")
    room_name = db.Column(db.String(255), default="未命名", comment="房间名称")
    room_password = db.Column(db.String(255), default="", comment="房间密码")
    user = db.Column(db.Integer, comment="房主")


class LiveRoom(BaseModel):
    """直播间"""
    __tablename__ = "mf_live_room"
    stream_id = db.Column(db.Integer, comment="直播流ID")
    user = db.Column(db.Integer, comment="用户ID")

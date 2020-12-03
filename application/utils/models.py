from application import db
from datetime import datetime
class BaseModel(db.Model):
    """公共模型"""
    __abstract__ = True # 抽象模型
    id = db.Column(db.Integer, primary_key=True, comment="主键ID")
    name = db.Column(db.String(255), default="", comment="名称/标题")
    is_deleted = db.Column(db.Boolean, default=False, comment="逻辑删除")
    orders = db.Column(db.Integer, default=0, comment="排序")
    status = db.Column(db.Boolean, default=True, comment="状态(是否显示,是否激活)")
    created_time = db.Column(db.DateTime, default=datetime.now, comment="创建时间")
    updated_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.name)
from application.utils.models import BaseModel, db


class Goods(BaseModel):
    """商品基本信息"""
    __tablename__ = "mf_goods"
    PROP_TYPE = (
        (0, "果树"),
        (1, "宠物"),
        (2, "植物生长道具"),
        (3, "宠物粮"),
    )
    remark = db.Column(db.String(255), comment="商品描述")
    price = db.Column(db.Numeric(7, 2), comment="商品价格[余额]")
    prop_type = db.Column(db.Integer, default=0, comment="道具类型")
    credit = db.Column(db.Integer, comment="商品价格[果子]")
    image = db.Column(db.String(255), comment="商品图片")


class Setting(BaseModel):
    """参数信息"""
    __tablename__ = "mf_orchard_setting"
    title = db.Column(db.String(255), comment="提示文本")
    value = db.Column(db.String(255), comment="数值")




from application.utils.models import BaseModel, db


class Goods(BaseModel):
    """商品基本信息"""
    __tablename__ = "mf_goods"
    remark = db.Column(db.String(255), comment="商品描述")
    price = db.Column(db.Numeric(7, 2), comment="商品价格[余额]")
    credit = db.Column(db.Integer, comment="商品价格[果子]")
    image = db.Column(db.String(255), comment="商品图片")





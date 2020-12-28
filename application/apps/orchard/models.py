from application.utils.models import BaseModel,db
class Goods(BaseModel):
    """商品基本信息"""
    __tablename__ = "mf_goods"
    remark = db.Column(db.String(255), comment="商品描述")
    price = db.Column(db.Numeric(7,2), comment="商品价格")
    image = db.Column(db.String(255),  comment="商品图片")
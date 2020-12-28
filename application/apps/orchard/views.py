from application import jsonrpc
from application.utils.language.status import APIStatus as status
from application.utils.language.message import ErrorMessage as message
from application import redis
from .models import Goods
from application.apps.users.models import User
from flask_jwt_extended import jwt_required, get_jwt_identity
from .marshmallow import GoodsInfoSchema


@jsonrpc.method(name="Orchard.goods.list")
@jwt_required  # 验证jwt
def goods_list(page=1, limit=10):
    """商品列表"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if user is None:
        return {
            "errno": status.CODE_NO_USER,
            "errmsg": message.user_not_exists,
        }

    pagination = Goods.query.filter(
        Goods.is_deleted == False,
        Goods.status == True
    ).paginate(page, per_page=limit)

    # 转换数据格式
    gis = GoodsInfoSchema()
    goods_list = gis.dump(pagination.items, many=True)

    return {
        "errno": status.CODE_OK,
        "errmsg": message.ok,
        "goods_list": goods_list,
        "pages": pagination.pages
    }

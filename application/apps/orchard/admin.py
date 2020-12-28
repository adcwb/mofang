# 根据模型自动生成页面
from .models import Goods
from flask_admin.contrib.sqla import ModelView
from application import admin, db


class GoodsAdminModel(ModelView):
    # 列表页显示字段列表
    column_list = ["id", "name", "price"]
    # 列表页可以直接编辑的字段列表
    column_editable_list = ["price"]
    # 是否允许查看详情
    can_view_details = True
    # 列表页显示直接可以搜索数据的字典
    column_searchable_list = ['name', 'price']
    # 过滤器
    column_filters = ['name']
    # 单页显示数据量
    page_size = 10


admin.add_view(GoodsAdminModel(Goods, db.session, name="商品", category="种植园"))

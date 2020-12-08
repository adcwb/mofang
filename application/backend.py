from application import admin
from flask_admin import AdminIndexView
# 修改admin站点标题
admin.name = "魔方APP"

# admin站点的默认首页信息
admin._set_admin_index_view(index_view=AdminIndexView(
    name="Home",
    template="admin/home.html",
))
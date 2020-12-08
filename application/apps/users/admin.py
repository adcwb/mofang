from flask_admin import BaseView,expose
from application import admin,db

# 自定义导航页面
# class UserAdmin(BaseView):
#     @expose("/")
#     def index(self):
#         title = "admin站点用户相关的内容"
#         data = locals()
#         data.pop("self")
#         return self.render(template="admin/user/index.html",**data)
#
# admin.add_view(UserAdmin(name='用户',url="user"))

# 根据模型自动生成页面
from .models import User
from flask_admin.contrib.sqla import ModelView
class UserAdminModel(ModelView):
    # 列表页显示字段列表
    column_list = ["id","name","nickname"]
    # 列表页显示排除字段列表
    # column_exclude_list = ["is_delete"]
    # 列表页可以直接编辑的字段列表
    column_editable_list = ["nickname"]
    # 是否允许查看详情
    can_view_details = True
    # 列表页显示直接可以搜索数据的字典
    column_searchable_list = ['nickname','name', 'email']
    # 过滤器
    column_filters = ['sex']
    # 单页显示数据量
    page_size = 10


# admin.add_view(UserAdminModel(User,db.session,name="用户")) # 把当前页面作为顶级导航进行显示
admin.add_view(UserAdminModel(User,db.session,name="用户", category="用户管理")) # 把当前页面添加到顶级导航下，category来设置，如果导航不存在，则自动创建

# 添加子导航还有种方式： 添加超链接作为导航
from flask_admin.menu import MenuLink
admin.add_link(MenuLink(name='老男孩', url='http://www.oldboyedu.com', category='用户管理')) # 把超链接作为子导航加载到顶级导航中
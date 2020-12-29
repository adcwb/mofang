from application.utils.models import BaseModel, db
from werkzeug.security import generate_password_hash, check_password_hash


class User(BaseModel):
    """用户基本信息表"""
    __tablename__ = "mf_user"
    name = db.Column(db.String(255), index=True, comment="用户账户")
    nickname = db.Column(db.String(255), comment="用户昵称")
    _password = db.Column(db.String(255), comment="登录密码")
    _transaction_password = db.Column(db.String(255), comment="交易密码")
    age = db.Column(db.SmallInteger, comment="年龄")
    money = db.Column(db.Numeric(7, 2), comment="账户余额")
    credit = db.Column(db.Numeric(7, 2), default=0, comment="果子积分")
    ip_address = db.Column(db.String(255), default="", index=True, comment="登录IP")
    intro = db.Column(db.String(500), default="", comment="个性签名")
    avatar = db.Column(db.String(255), default="", comment="头像url地址")
    sex = db.Column(db.SmallInteger, default=0, comment="性别")  # 0表示未设置,保密, 1表示男,2表示女
    email = db.Column(db.String(32), index=True, default="", nullable=False, comment="邮箱地址")
    mobile = db.Column(db.String(32), index=True, nullable=False, comment="手机号码")
    unique_id = db.Column(db.String(255), index=True, default="", comment="客户端唯一标记符")
    province = db.Column(db.String(255), default="", comment="省份")
    city = db.Column(db.String(255), default="", comment="城市")
    area = db.Column(db.String(255), default="", comment="地区")
    info = db.relationship('UserProfile', backref='user', uselist=False)

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, rawpwd):
        """密码加密"""
        self._password = generate_password_hash(rawpwd)

    def check_password(self, rawpwd):
        """验证密码"""
        return check_password_hash(self.password, rawpwd)

    @property
    def transaction_password(self):
        return self._transaction_password

    @transaction_password.setter
    def transaction_password(self, rawpwd):
        """密码加密"""
        self._transaction_password = generate_password_hash(rawpwd)

    def check_transaction_password(self, rawpwd):
        """验证密码"""
        return check_password_hash(self.transaction_password, rawpwd)


class UserProfile(BaseModel):
    """用户详情信息表"""
    __tablename__ = "mf_user_profile"
    user_id = db.Column(db.Integer, db.ForeignKey('mf_user.id'), comment="用户ID")
    education = db.Column(db.Integer, comment="学历教育")
    middle_school = db.Column(db.String(255), default="", comment="初中/中专")
    high_school = db.Column(db.String(255), default="", comment="高中/高职")
    college_school = db.Column(db.String(255), default="", comment="大学/大专")
    profession_cate = db.Column(db.String(255), default="", comment="职业类型")
    profession_info = db.Column(db.String(255), default="", comment="职业名称")
    position = db.Column(db.SmallInteger, default=0, comment="职位/职称")
    emotion_status = db.Column(db.SmallInteger, default=0, comment="情感状态")
    birthday = db.Column(db.DateTime, default="", comment="生日")
    hometown_province = db.Column(db.String(255), default="", comment="家乡省份")
    hometown_city = db.Column(db.String(255), default="", comment="家乡城市")
    hometown_area = db.Column(db.String(255), default="", comment="家乡地区")
    hometown_address = db.Column(db.String(255), default="", comment="家乡地址")
    living_province = db.Column(db.String(255), default="", comment="现居住省份")
    living_city = db.Column(db.String(255), default="", comment="现居住城市")
    living_area = db.Column(db.String(255), default="", comment="现居住地区")
    living_address = db.Column(db.String(255), default="", comment="现居住地址")

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.user.name)


# class UserRelation(BaseModel):
#     """用户关系"""
#     __tablename__ = "mf_user_relation"
#     relration_chioce = (
#         (1, "已申请"),
#         (2, "已通过"),
#         (3, "已超时"),
#         (4, "已拒绝"),
#         (5, "已取消"),
#         (6, "已关注"),
#         (7, "取消关注"),
#         (8, "拉黑"),  # 正向拉黑
#         (9, "拉黑"),  # 反向拉黑
#         (10, "取消拉黑")
#     )
#     send_user = db.Column(db.Integer, comment="用户ID1")  # 主动构建关系的用户
#     receive_user = db.Column(db.Integer, comment="用户ID2")  # 接受关系请求的用户
#     # 创建方式的类型
#     # 查找  1.手机 2.账号 3.邮箱 3.昵称
#     # 社交  3.群聊
#     # 推荐  4.同城推荐 5. 二维码邀请注册
#     relation_type = db.Column(db.Integer, default=0, comment="构建关系类型")
#     # 关系的状态
#
#     status = db.Column(db.Integer, default=0, comment="关系状态")
#
#     def __repr__(self):
#         return "用户%s通过%s对%s进行了%s操作" % (self.send_user, self.relation_type, self.receive_user, self.status)


class UserRelation(BaseModel):
    """用户关系"""
    __tablename__ = "mf_user_relation"
    relation_status_chioce = (
        (1, "好友"),
        (2, "关注"),
        (3, "拉黑"),
    )
    relation_type_chioce = (
        (1, "手机"),
        (2, "账号"),
        (3, "邮箱"),
        (4, "昵称"),
        (5, "群聊"),
        (6, "二维码邀请注册"),
    )
    send_user = db.Column(db.Integer, comment="用户1")  # 主动构建关系的用户
    receive_user = db.Column(db.Integer, comment="用户2")  # 接受关系请求的用户
    relation_type = db.Column(db.Integer, default=0, comment="构建关系类型")
    relation_status = db.Column(db.Integer, default=0, comment="关系状态")

    def __repr__(self):
        return "用户%s通过%s对%s进行了%s操作" % (self.send_user, self.relation_type, self.receive_user, self.relation_status)


class Recharge(BaseModel):
    __tablename__ = "mf_user_recharge"
    status = db.Column(db.Boolean, default=True, comment="状态(是否支付)")
    out_trade_number = db.Column(db.String(64), unique=True, comment="订单号")
    user_id = db.Column(db.Integer, comment="用户")
    money = db.Column(db.Numeric(7, 2), comment="账户余额")
    trade_number = db.Column(db.String(64), default="",  index=True, comment="流水号")

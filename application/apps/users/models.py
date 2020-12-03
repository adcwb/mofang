from application.utils.models import BaseModel, db
from werkzeug.security import generate_password_hash, check_password_hash


class User(BaseModel):
    """用户基本信息表"""
    __tablename__ = "mf_user"
    name = db.Column(db.String(255), index=True, comment="用户账户")
    nickname = db.Column(db.String(255), comment="用户昵称")
    _password = db.Column(db.String(255), comment="登录密码")
    age = db.Column(db.SmallInteger, comment="年龄")
    money = db.Column(db.Numeric(7, 2), comment="账户余额")
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

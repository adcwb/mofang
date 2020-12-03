from marshmallow import Schema, fields, validate, ValidationError, post_load
from application.apps.users.models import User, UserProfile


class UserProfileSchema(Schema):
    education = fields.Integer()
    middle_school = fields.String()


class UserSchema(Schema):
    name = fields.String()
    age = fields.Integer()
    email = fields.Email()
    money = fields.Number()
    info = fields.Nested(UserProfileSchema, only=["middle_school"])

    class Meta:
        fields = ["name", "age", "money", "email", "info"]
        ordered = True  # 转换成有序字典

class UserSchema2(Schema):
    name = fields.String()
    sex = fields.String()
    age = fields.Integer(missing=18)
    email = fields.Email()
    mobile = fields.String(required=True)

    @post_load
    def post_load(self, data, **kwargs):
        return User(**data)



def index():
    """序列化"""
    """单个模型数据的序列化处理"""
    # user1 = User(name="xiaoming", password="123456", age=16, email="333@qq.com", money=31.50)
    # # print(user1)
    # # 把模型对象转换成字典格式
    # data1 = UserSchema().dump(user1)
    # print(type(data1), data1)
    #
    # # 把模型对象转换成json字符串格式
    # data2 = UserSchema().dumps(user1)
    # print(type(data2), data2)

    # """多个模型数据的序列化"""
    # user1 = User(name="xiaoming", password="123456", age=15, email="333@qq.com", money=31.50)
    # user2 = User(name="xiaohong", password="123456", age=16, email="333@qq.com", money=31.50)
    # user3 = User(name="xiaopang", password="123456", age=17, email="333@qq.com", money=31.50)
    # data_list = [user1, user2, user3]
    # data1 = UserSchema(many=True).dumps(data_list)
    # print(type(data1), data1)

    # """序列化嵌套使用"""
    # user1 = User(name="xiaoming", password="123456", age=15, email="333@qq.com", money=31.50)
    # user1.info = UserProfile(
    #     education=3,
    #     middle_school="北京师范学院附属中学白沙路分校"
    # )
    # data = UserSchema().dump(user1)
    # data = UserSchema().dumps(user1)
    # print(data)

    """反序列化"""
    # user_data = {"mobile": "1331345635", "name": "xiaoming", "email": "xiaoming@qq.com", "sex": "abc"}
    # us2 = UserSchema2()
    # result = us2.load(user_data)
    # print(result)

    """忽略部分数据partial=True"""
    user_data = {"name": "xiaoming", "sex": "abc"}
    us2 = UserSchema2()
    result = us2.load(user_data, partial=True)
    print(result)

    return "ok"
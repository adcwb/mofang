from . import InitConfig


class Config(InitConfig):
    """
    项目开发环境下的配置
    """
    DEBUG = True
    # 数据库连接设置
    SQLALCHEMY_DATABASE_URI = "mysql://mofang:123456@127.0.0.1:3306/mofang?charset=utf8mb4"
    # 是否显示原生SQL语句
    SQLALCHEMY_ECHO = False

    # redis
    REDIS_URL = "redis://@127.0.0.1:6379/0"

    # session存储配置
    SESSION_REDIS_HOST = "127.0.0.1"
    SESSION_REDIS_PORT = 6379
    # SESSION_REDIS_PWD = 123456
    SESSION_REDIS_DB = 1

    # 日志配置
    LOG_LEVEL = "DEBUG"  # 日志输出到文件中的最低等级
    LOG_DIR = "/logs/mofang.log"  # 日志存储目录
    LOG_MAX_BYTES = 300 * 1024 * 1024  # 单个日志文件的存储上限[单位: b]
    LOG_BACKPU_COUNT = 20  # 日志文件的最大备份数量
    LOG_NAME = "mofang"  # 日志器名称

    # 注册蓝图
    INSTALLED_APPS = [
        "home",
        "users",
        "marsh",
        "application.apps.orchard",
        "application.apps.live",
    ]

    # 阿里云短信接口
    AccessKeyId = 'LTAI4GEHoHTajnEZkFrtVHS7'
    AccessKeySecret = 'dA41aMsNPOQWHSFdOaRxhgs5YLeewG'

    SMS_ACCOUNT_ID = "8aaf0708754a3ef201756431501007cf"  # 接口主账号
    SMS_ACCOUNT_TOKEN = "df681913a8144346a6df66eb014c2eec"  # 认证token令牌
    SMS_APP_ID = "8aaf0708754a3ef20175643150fa07d5"  # 应用ID
    SMS_TEMPLATE_ID = 1  # 短信模板ID
    SMS_EXPIRE_TIME = 60 * 5  # 短信有效时间，单位:秒/s
    SMS_INTERVAL_TIME = 300  # 短信发送冷却时间，单位:秒/s

    # jwt 相关配置
    # 加密算法,默认: HS256
    JWT_ALGORITHM = "HS256"
    # 秘钥，默认是flask配置中的SECRET_KEY
    JWT_SECRET_KEY = "y58Rsqzmts6VCBRHes1Sf2DHdGJaGqPMi6GYpBS4CKyCdi42KLSs9TQVTauZMLMw"
    # token令牌有效期，单位: 秒/s，默认:　datetime.timedelta(minutes=15) 或者 15 * 60
    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60
    # refresh刷新令牌有效期，单位: 秒/s，默认：datetime.timedelta(days=30) 或者 30*24*60*60
    JWT_REFRESH_TOKEN_EXPIRES = 30 * 24 * 60 * 60
    # 设置通过哪种方式传递jwt，默认是http请求头，也可以是query_string，json，cookies
    JWT_TOKEN_LOCATION = ["headers", "query_string"]
    # 当通过http请求头传递jwt时，请求头参数名称设置，默认值： Authorization
    JWT_HEADER_NAME = "Authorization"
    # 当通过查询字符串传递jwt时，查询字符串的参数名称设置，默认：jwt
    JWT_QUERY_STRING_NAME = "token"
    # 当通过http请求头传递jwt时，令牌的前缀。
    # 默认值为 "Bearer"，例如：Authorization: Bearer <JWT>
    JWT_HEADER_TYPE = "jwt"

    # 防水墙验证码
    CAPTCHA_GATEWAY = "https://ssl.captcha.qq.com/ticket/verify"
    CAPTCHA_APP_ID = "2048217533"
    CAPTCHA_APP_SECRET_KEY = "0OnRy4X4QjGZqxXnahF2fSQ**"

    # mongoDB配置信息
    # MONGO_URI = "mongodb://mofang:123456@127.0.0.1:27017/mofang"
    MONGO_URI = "mongodb://127.0.0.1:27017/mofang"

    # 用户默认头像
    DEFAULT_AVATAR = "95822582-39d8-43ce-9498-fdced7f6a144.jpeg"
    # 服务端带外提供的url地址
    # SERVER_URL = "http://127.0.0.1:5000"

    # socketio
    CORS_ALLOWED_ORIGINS = "*"
    ASYNC_MODE = None
    HOST = "0.0.0.0"
    PORT = 5000

    # 支付宝配置信息
    ALIPAY_APP_ID = "2016102600767166"
    ALIPAY_SIGN_TYPE = "RSA2"
    ALIPAY_NOTIFY_URL = "http://127.0.0.1:5000/alipay/notify"
    ALIPAY_SANDBOX = True

    # ossrs 服务端
    SRS_HTTP_API = "http://127.0.0.1:1985/api/v1/"

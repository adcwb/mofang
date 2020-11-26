class InitConfig():
    """
    项目默认初始化配置
    """
    # 调试模式
    DEBUG = True

    # 数据库相关配置
    SQLALCHEMY_DATABASE_URI = ""
    # 动态追踪修改设置
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 查询时会显示原始SQL语句
    SQLALCHEMY_ECHO = True

    # redis数据库配置
    REDIS_URL = ""

    # 设置密钥，可以通过 base64.b64encode(os.urandom(48)) 来生成一个指定长度的随机字符串
    SECRET_KEY = "WlWIZofhDzjpmpXlfasxw8FeNbehkKIr0tJ6GOL/SbJfGjqmoTbSxIkvCW7ThEGt"

    # session存储配置
    # session存储方式配置
    SESSION_TYPE = "redis"
    # 如果设置session的生命周期是否是会话期, 为True，则关闭浏览器session就失效
    SESSION_PERMANENT = False
    # 设置session_id在浏览器中的cookie有效期
    PERMANENT_SESSION_LIFETIME = 24 * 60 * 60  # session 的有效期，单位是秒
    # 是否对发送到浏览器上session的cookie值进行加密
    SESSION_USE_SIGNER = True
    # 保存到redis的session数的名称前缀
    SESSION_KEY_PREFIX = "session:"
    # session保存数据到redis时启用的链接对象
    SESSION_REDIS = None  # 用于连接redis的配置

    SESSION_REDIS_HOST = "127.0.0.1"
    SESSION_REDIS_PORT = 6379
    SESSION_REDIS_PWD = 123456
    SESSION_REDIS_DB = 0

    # 调整json数据转换中文的配置
    JSON_AS_ASCII = False

    # 日志相关配置
    LOG_LEVEL = "INFO"  # 日志输出到文件中的最低等级
    LOG_DIR = "logs/0.log"  # 日志存储目录
    LOG_MAX_BYTES = 300 * 1024 * 1024  # 单个日志文件的存储上限[单位: b]
    LOG_BACKPU_COUNT = 20  # 日志文件的最大备份数量
    LOG_NAME = "flask"  # 日志器的名字

    # 蓝图注册列表
    INSTALLED_APPS = [

    ]

    # 总路由路径
    URL_PATH = "application.urls"

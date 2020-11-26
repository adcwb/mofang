from . import InitConfig


class Config(InitConfig):
    """
    项目开发环境下的配置
    """
    DEBUG = True
    # 数据库连接设置
    SQLALCHEMY_DATABASE_URI = "mysql://mofang:123456@127.0.0.1:3306/mofang?charset=utf8mb4"
    # 是否显示原生SQL语句
    SQLALCHEMY_ECHO = True

    # redis
    REDIS_URL = "redis://123456@127.0.0.1:6379/0"

    # session存储配置
    SESSION_REDIS_HOST = "127.0.0.1"
    SESSION_REDIS_PORT = 6379
    SESSION_REDIS_PWD = 123456
    SESSION_REDIS_DB = 1

    # 日志配置
    LOG_LEVEL = "DEBUG"  # 日志输出到文件中的最低等级
    LOG_DIR = "/logs/mofang.log"  # 日志存储目录
    LOG_MAX_BYTES = 300 * 1024 * 1024  # 单个日志文件的存储上限[单位: b]
    LOG_BACKPU_COUNT = 20  # 日志文件的最大备份数量
    LOG_NAME = "mofang"  # 日志器名称

    # 注册蓝图
    INSTALLED_APPS = [
        "application.apps.home",
    ]

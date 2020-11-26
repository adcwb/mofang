import logging
from logging.handlers import RotatingFileHandler


class Log():
    """日志模块"""

    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        return self.setup()

    def setup(self):
        """安装日志功能到flask中"""
        # 设置日志的记录等级
        logging.basicConfig(level=self.app.config.get("LOG_LEVEL"))  # 调试debug级

        # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
        file_log_handler = RotatingFileHandler(
            self.app.BASE_DIR + self.app.config.get("LOG_DIR"),
            maxBytes=self.app.config.get("LOG_MAX_BYTES"),
            backupCount=self.app.config.get("LOG_BACKPU_COUNT")
        )

        # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
        formatter = logging.Formatter('%(name)s: %(levelname)s %(asctime)s %(filename)s:%(lineno)d %(message)s')
        # 为刚创建的日志记录器设置日志记录格式
        file_log_handler.setFormatter(formatter)

        # 为全局的日志工具对象（flaskapp使用的）添加日志记录器
        logging.getLogger(self.app.config.get("LOG_NAME")).addHandler(file_log_handler)
        # 返回日志器对象提供给业务开发
        logger = logging.getLogger(self.app.config.get("LOG_NAME"))
        return logger

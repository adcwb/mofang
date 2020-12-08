import os
import sys
import logging

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_script import Manager
from flask_sqlalchemy import SQLAlchemy
from flask_redis import FlaskRedis
from flask_session import Session
from flask_migrate import Migrate, MigrateCommand
from flask_jsonrpc import JSONRPC
from flask_marshmallow import Marshmallow
from flask_admin import Admin, AdminIndexView
from flask_babelex import Babel
from faker import Faker

from application.utils.config import load_config
from application.utils.session import init_session
from application.utils.logger import Log
from application.utils.commands import load_command
from application.utils import init_blueprint

# 创建终端脚本管理对象
manager = Manager()

# 创建数据库链接对象
db = SQLAlchemy()

# redis链接对象
redis = FlaskRedis()

# Session存储对象
session_store = Session()

# 数据迁移实例对象
migrate = Migrate()

# 日志对象
log = Log()

# jsonrpc模块实例化对象
jsonrpc = JSONRPC(service_url="/api")

# 数据转换器的对象创建
ma = Marshmallow()

# jwt认证模块实例化
jwt = JWTManager()

# flask-admin模块实例化
admin = Admin()

# flask-babelex模块实例化
babel = Babel()

def init_app(config_path):
    """
    全局初始化
    :return:
    """
    # 创建app应用对象
    app = Flask(__name__)

    # 项目根目录
    app.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 加载导包路径
    sys.path.insert(0, os.path.join(app.BASE_DIR, "application/utils/language"))


    # 加载配置
    Config = load_config(config_path)
    app.config.from_object(Config)

    # 数据库初始化
    db.init_app(app)
    redis.init_app(app)

    # 数据转换器的初始化，必须放在db初始化的后面
    ma.init_app(app)

    # session存储初始化
    init_session(app)
    session_store.init_app(app)

    # 数据迁移初始化
    migrate.init_app(app, db)
    # 添加数据迁移的命令到终端脚本工具中
    manager.add_command('db', MigrateCommand)

    # 日志初始化
    app.log = log.init_app(app)

    # 初始化终端脚本工具
    manager.app = app

    # 注册自定义命令
    load_command(manager)

    # 蓝图注册
    init_blueprint(app)

    # 初始化json-rpc
    jsonrpc.init_app(app)

    # jwt初始化
    jwt.init_app(app)

    # admin站点
    admin.init_app(app)

    # 项目语言
    babel.init_app(app)

    # 数据种子生成器[faker]
    app.faker = Faker(app.config.get("LANGUAGE"))

    return manager

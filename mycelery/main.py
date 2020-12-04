from __future__ import absolute_import
from celery import Celery
from application import init_app

# 初始化celery对象
app = Celery("flask")

# 初始化flask
flask_app = init_app("application.settings.dev").app

# 加载配置
app.config_from_object("mycelery.config")
# 自动注册任务
app.autodiscover_tasks(["mycelery.sms"])
# 运行celery
# 主程序终端下启动: celery -A mycelery.main worker -l info
# 调度器终端下启动: celery -A mycelery.main beat

from .main import app
# 任务队列地址
broker_url = 'redis://127.0.0.1:6379/15'
# 结果队列地址
result_backend = "redis://127.0.0.1:6379/14"
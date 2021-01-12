# 任务队列地址
broker_url = 'redis://127.0.0.1:6379/15'
# 结果队列地址
result_backend = "redis://127.0.0.1:6379/14"

# 周期任务
from mycelery.main import app

app.conf.beat_schedule = {
    # Executes every Monday morning at 7:30 a.m.
    'tree_write_task': {
        'task': 'tree_write',
        'schedule': 5,
    },
}

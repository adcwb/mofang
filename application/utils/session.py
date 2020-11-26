from redis import Redis


def init_session(app):
    """
    配置session存储到redis数据库中
    :param app:
    :return:
    """
    host = app.config.get("SESSION_REDIS_HOST", "127.0.0.1")
    port = app.config.get("SESSION_REDIS_PORT", 6379)
    passwd = app.config.get("SESSION_REDIS_PWD", 123456)
    db = app.config.get("SESSION_REDIS_DB", 0)
    app.config["SESSION_REDIS"] = Redis(host=host, port=port, password=passwd, db=db)

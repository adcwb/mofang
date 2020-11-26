from application import init_app
from flask import session
manage = init_app("application.settings.dev")


@manage.app.route("/")
def index():
    session["username"] = "xiaoming"
    return "success"


if __name__ == '__main__':
    manage.run()

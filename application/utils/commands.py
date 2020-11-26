import os
from importlib import import_module
from flask_script import Command, Option
import inspect


def load_command(manager, command_path=None):
    """自动加载自定义终端命令"""
    if command_path is None:
        command_path = "application.utils.commands"

    module = import_module(command_path)
    class_list = inspect.getmembers(module, inspect.isclass)
    for class_item in class_list:
        if issubclass(class_item[1], Command) and class_item[0] != "Command":
            manager.add_command(class_item[1].name, class_item[1])


class BlueprintCommand(Command):
    """
    蓝图生成命令
    """
    name = "blue"
    option_list = [
        Option('--name', '-n', dest='name'),
    ]

    def run(self, name):
        # 生成蓝图名称对象的目录
        os.mkdir(name)
        open("%s/__init__.py" % name, "w")
        open("%s/views.py" % name, "w")
        open("%s/models.py" % name, "w")
        with open("%s/urls.py" % name, "w") as f:
            content = """from . import views
from application.utils import path
urlpatterns = [

]"""
            f.write(content)
        print("蓝图%s创建完成...." % name)

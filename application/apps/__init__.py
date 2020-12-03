import os


apps_path = os.path.dirname(__file__)


apps_path = apps_path.split("/")
apps_path = apps_path[-2] + "." + apps_path[-1]



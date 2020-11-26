from . import views
from application.utils import path

urlpatterns = [
    path("/", views.index),
]

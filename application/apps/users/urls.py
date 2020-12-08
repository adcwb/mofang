from . import views
from application.utils import path
urlpatterns = [
    path("/avatar", views.avatar),
]
from application.utils import include

urlpatterns = [
    include("/home", "home.urls"),
    include("/users", "users.urls"),
    include("/marsh", "marsh.urls"),
    include("/orchard", "orchard.urls"),
    include("/live", "live.urls"),
]

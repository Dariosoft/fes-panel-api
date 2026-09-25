from django.urls import include, path

from shops.views import live, panel, ready

urlpatterns = [
    path("panel", panel),
    path("panel/", include("identity.urls")),
    path("health/live", live),
    path("health/ready", ready),
]

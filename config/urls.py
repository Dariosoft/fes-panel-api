from django.urls import path

from shops.views import live, panel, ready

urlpatterns = [
    path("panel", panel),
    path("health/live", live),
    path("health/ready", ready),
]

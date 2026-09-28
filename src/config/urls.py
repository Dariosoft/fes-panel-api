from django.urls import include, path

from common.health.views import live, ready

urlpatterns = [
    path("panel/", include("identity.api.urls")),
    path("health/live", live),
    path("health/ready", ready),
]

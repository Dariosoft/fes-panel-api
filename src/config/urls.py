from django.urls import include, path

from common.health.views import live, ready
from common.panel.views import panel

urlpatterns = [
    path("panel", panel),
    path("panel/", include("identity.api.urls")),
    path("health/live", live),
    path("health/ready", ready),
]

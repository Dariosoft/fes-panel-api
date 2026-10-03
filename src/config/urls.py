from django.urls import include, path

from common.health.views import live, ready

urlpatterns = [
    path("panel/identity/", include("identity.api.urls")),
    path("panel/catalog/", include("catalog.api.urls")),
    path("health/live", live),
    path("health/ready", ready),
]

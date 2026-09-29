from django.urls import path

from identity.api.views import GoogleLoginRedirectView, PanelSessionViewSet

urlpatterns = [
    path("login/google", GoogleLoginRedirectView.as_view(), name="panel-login-google"),
    path(
        "session",
        PanelSessionViewSet.as_view({"get": "retrieve", "delete": "destroy"}),
        name="panel-session",
    ),
]

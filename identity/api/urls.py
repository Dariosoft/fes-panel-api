from django.urls import path

from identity.api.views import GoogleLoginRedirectView, PanelLogoutView, PanelSessionView

urlpatterns = [
    path("login/google", GoogleLoginRedirectView.as_view(), name="panel-login-google"),
    path("session", PanelSessionView.as_view(), name="panel-session"),
    path("logout", PanelLogoutView.as_view(), name="panel-logout"),
]

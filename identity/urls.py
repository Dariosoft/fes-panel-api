from django.urls import path

from identity.views import LoginView, LogoutView, WhoAmIView

urlpatterns = [
    path("me", WhoAmIView.as_view(), name="panel-whoami"),
    path("session/logout", LogoutView.as_view(), name="panel-logout"),
    path("session/google", LoginView.as_view(), name="panel-login-google"),
]

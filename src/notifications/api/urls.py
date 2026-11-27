from django.urls import path

from notifications.api.views import PanelFeedView

urlpatterns = [
    path("feed", PanelFeedView.as_view(), name="panel-notifications-feed"),
]

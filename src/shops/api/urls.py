from django.urls import path

from shops.api.views import PanelShopView

urlpatterns = [
    path("", PanelShopView.as_view(), name="panel-shop"),
]

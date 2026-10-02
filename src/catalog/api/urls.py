from django.urls import path

from catalog.api.views import PanelCatalogProductViewSet, PanelCatalogPublishView

urlpatterns = [
    path(
        "products",
        PanelCatalogProductViewSet.as_view({"get": "list", "post": "create"}),
        name="panel-catalog-products",
    ),
    path(
        "products/<str:product_id>",
        PanelCatalogProductViewSet.as_view({"put": "update", "delete": "destroy"}),
        name="panel-catalog-product",
    ),
    path(
        "products/<str:product_id>/publish",
        PanelCatalogProductViewSet.as_view({"post": "publish"}),
        name="panel-catalog-product-publish",
    ),
    path(
        "products/<str:product_id>/unpublish",
        PanelCatalogProductViewSet.as_view({"post": "unpublish"}),
        name="panel-catalog-product-unpublish",
    ),
    path(
        "publish",
        PanelCatalogPublishView.as_view(),
        name="panel-catalog-publish",
    ),
]

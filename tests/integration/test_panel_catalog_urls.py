from django.test import SimpleTestCase
from django.urls import resolve

from catalog.api.views import PanelCatalogProductViewSet, PanelCatalogPublishView
from common.health.views import live, ready


class PanelCatalogUrlTests(SimpleTestCase):
    def test_product_collection_routes(self):
        match = resolve("/panel/catalog/products")
        self.assertIs(match.func.cls, PanelCatalogProductViewSet)
        self.assertEqual(match.func.actions["get"], "list")
        self.assertEqual(match.func.actions["post"], "create")

    def test_product_item_routes(self):
        match = resolve("/panel/catalog/products/p1")
        self.assertIs(match.func.cls, PanelCatalogProductViewSet)
        self.assertEqual(match.func.actions["put"], "update")
        self.assertEqual(match.func.actions["delete"], "destroy")
        self.assertEqual(match.kwargs, {"product_id": "p1"})

    def test_publish_and_unpublish_product_routes(self):
        publish = resolve("/panel/catalog/products/p1/publish")
        self.assertEqual(publish.func.actions, {"post": "publish"})
        self.assertEqual(publish.kwargs, {"product_id": "p1"})

        unpublish = resolve("/panel/catalog/products/p1/unpublish")
        self.assertEqual(unpublish.func.actions, {"post": "unpublish"})

    def test_publish_catalog_route(self):
        match = resolve("/panel/catalog/publish")
        self.assertIs(match.func.cls, PanelCatalogPublishView)

    def test_identity_routes_are_preserved(self):
        self.assertEqual(resolve("/panel/identity/session").url_name, "panel-session")

    def test_health_routes_are_preserved(self):
        self.assertEqual(resolve("/health/live").func, live)
        self.assertEqual(resolve("/health/ready").func, ready)

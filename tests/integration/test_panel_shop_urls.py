from django.test import SimpleTestCase
from django.urls import resolve

from common.health.views import live, ready
from shops.api.views import PanelShopView


class PanelShopUrlTests(SimpleTestCase):
    def test_shop_route_resolves_to_panel_shop_view(self):
        match = resolve("/panel/shop")

        self.assertIs(match.func.cls, PanelShopView)
        self.assertEqual(match.url_name, "panel-shop")

    def test_shop_view_exposes_get_and_put(self):
        self.assertTrue(callable(getattr(PanelShopView, "get", None)))
        self.assertTrue(callable(getattr(PanelShopView, "put", None)))

    def test_identity_routes_are_preserved(self):
        self.assertEqual(resolve("/panel/identity/session").url_name, "panel-session")

    def test_catalog_routes_are_preserved(self):
        match = resolve("/panel/catalog/products")
        self.assertEqual(match.url_name, "panel-catalog-products")

    def test_health_routes_are_preserved(self):
        self.assertEqual(resolve("/health/live").func, live)
        self.assertEqual(resolve("/health/ready").func, ready)

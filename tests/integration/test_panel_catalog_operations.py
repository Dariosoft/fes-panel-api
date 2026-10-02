from pathlib import Path
from unittest.mock import patch

from django.apps import apps
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIClient

from catalog.domain import SESSION_COOKIE_NAME
from catalog.dtos import CatalogResponse, PanelSession


class _SessionGateway:
    def resolve(self, fes_session: str | None) -> PanelSession:
        return PanelSession(authenticated=True, account_id="acc-session")


class _CatalogGateway:
    def __init__(self, response: CatalogResponse | None = None):
        self._response = response or CatalogResponse(status_code=200, body={"ok": True})
        self.calls: list[tuple] = []

    def _record(self, name, *args):
        self.calls.append((name, *args))
        return self._response

    def list_products(self, owner_account_id):
        return self._record("list_products", owner_account_id)

    def create_product(self, owner_account_id, body, content_type):
        return self._record("create_product", owner_account_id, body, content_type)

    def update_product(self, owner_account_id, product_id, body, content_type):
        return self._record("update_product", owner_account_id, product_id, body, content_type)

    def delete_product(self, owner_account_id, product_id):
        return self._record("delete_product", owner_account_id, product_id)

    def publish_product(self, owner_account_id, product_id):
        return self._record("publish_product", owner_account_id, product_id)

    def unpublish_product(self, owner_account_id, product_id):
        return self._record("unpublish_product", owner_account_id, product_id)

    def publish_catalog(self, owner_account_id, body, content_type):
        return self._record("publish_catalog", owner_account_id, body, content_type)


class PanelCatalogOperationTests(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.cookies[SESSION_COOKIE_NAME] = "tok"

    def _run(self, method, path, catalog, **kwargs):
        with patch.multiple(
            "catalog.api.panel_session",
            build_session_gateway=lambda: _SessionGateway(),
            build_catalog_gateway=lambda: catalog,
        ):
            return getattr(self.client, method)(path, **kwargs)

    def test_list_products_forwards_owner(self):
        catalog = _CatalogGateway()
        self._run("get", "/panel/catalog/products", catalog)
        self.assertEqual(catalog.calls, [("list_products", "acc-session")])

    def test_create_product_forwards_owner_and_body(self):
        catalog = _CatalogGateway()
        self._run(
            "post",
            "/panel/catalog/products",
            catalog,
            data={"name": "camisa"},
            format="json",
        )
        name, owner, body, content_type = catalog.calls[0]
        self.assertEqual(name, "create_product")
        self.assertEqual(owner, "acc-session")
        self.assertIn(b"camisa", body)
        self.assertEqual(content_type, "application/json")

    def test_update_product_forwards_owner_id_and_body(self):
        catalog = _CatalogGateway()
        self._run(
            "put",
            "/panel/catalog/products/p1",
            catalog,
            data={"name": "nueva"},
            format="json",
        )
        name, owner, product_id, _body, content_type = catalog.calls[0]
        self.assertEqual((name, owner, product_id), ("update_product", "acc-session", "p1"))
        self.assertEqual(content_type, "application/json")

    def test_delete_product_forwards_owner_and_id(self):
        catalog = _CatalogGateway()
        self._run("delete", "/panel/catalog/products/p1", catalog)
        self.assertEqual(catalog.calls, [("delete_product", "acc-session", "p1")])

    def test_publish_product_forwards_owner_and_id(self):
        catalog = _CatalogGateway()
        self._run("post", "/panel/catalog/products/p1/publish", catalog)
        self.assertEqual(catalog.calls, [("publish_product", "acc-session", "p1")])

    def test_unpublish_product_forwards_owner_and_id(self):
        catalog = _CatalogGateway()
        self._run("post", "/panel/catalog/products/p1/unpublish", catalog)
        self.assertEqual(catalog.calls, [("unpublish_product", "acc-session", "p1")])

    def test_publish_catalog_forwards_owner_and_body(self):
        catalog = _CatalogGateway(response=CatalogResponse(status_code=200, body={"published": 2}))
        response = self._run(
            "post",
            "/panel/catalog/publish",
            catalog,
            data={"products": []},
            format="json",
        )
        name, owner, _body, content_type = catalog.calls[0]
        self.assertEqual(
            (name, owner, content_type), ("publish_catalog", "acc-session", "application/json")
        )
        self.assertEqual(response.json(), {"published": 2})

    def test_publish_catalog_without_products_is_200_with_zero(self):
        catalog = _CatalogGateway(response=CatalogResponse(status_code=200, body={"published": 0}))
        response = self._run(
            "post",
            "/panel/catalog/publish",
            catalog,
            data={"products": []},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"published": 0})

    @override_settings(
        PANEL_PUBLIC_ORIGIN="https://panel.example.com",
        CORS_ALLOWED_ORIGINS=["https://panel.example.com"],
        CORS_ALLOW_CREDENTIALS=True,
    )
    def test_cors_preflight_allows_panel_origin_with_credentials(self):
        response = self.client.options(
            "/panel/catalog/products",
            HTTP_ORIGIN="https://panel.example.com",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Access-Control-Allow-Origin"], "https://panel.example.com")
        self.assertEqual(response["Access-Control-Allow-Credentials"], "true")

    def test_health_live_still_responds(self):
        response = self.client.get("/health/live")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "live"})

    def test_catalog_has_no_model_or_migration(self):
        catalog_app = apps.get_app_config("catalog")
        self.assertEqual(list(catalog_app.get_models()), [])
        self.assertFalse((Path(catalog_app.path) / "migrations").exists())

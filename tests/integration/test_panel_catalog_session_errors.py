from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.test import APIClient

from catalog.domain import (
    SESSION_COOKIE_NAME,
    CatalogServiceUnavailable,
    SessionServiceUnavailable,
)
from catalog.dtos import CatalogResponse, PanelSession


class _SessionGateway:
    def __init__(self, authenticated=True, error=None):
        self._authenticated = authenticated
        self._error = error

    def resolve(self, fes_session: str | None) -> PanelSession:
        if self._error:
            raise self._error
        if not self._authenticated:
            return PanelSession(authenticated=False, account_id=None)
        return PanelSession(authenticated=True, account_id="acc-session")


class _CatalogGateway:
    def __init__(self, response=None, error=None):
        self._response = response or CatalogResponse(status_code=200, body={"ok": True})
        self._error = error
        self.calls: list[tuple] = []

    def _record(self, name, *args):
        self.calls.append((name, *args))
        if self._error:
            raise self._error
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


class PanelCatalogSessionErrorTests(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()

    def _patch(self, session, catalog):
        return patch.multiple(
            "catalog.api.panel_session",
            build_session_gateway=lambda: session,
            build_catalog_gateway=lambda: catalog,
        )

    def test_missing_cookie_is_401_without_forwarding(self):
        session = _SessionGateway(authenticated=False)
        catalog = _CatalogGateway()

        with self._patch(session, catalog):
            response = self.client.get("/panel/catalog/products")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"], "no_autenticado")
        self.assertEqual(catalog.calls, [])

    def test_anonymous_session_is_401_without_forwarding(self):
        session = _SessionGateway(authenticated=False)
        catalog = _CatalogGateway()
        self.client.cookies[SESSION_COOKIE_NAME] = "tok"

        with self._patch(session, catalog):
            response = self.client.get("/panel/catalog/products")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"], "no_autenticado")
        self.assertEqual(catalog.calls, [])

    def test_accounts_failure_is_503_without_forwarding(self):
        session = _SessionGateway(error=SessionServiceUnavailable())
        catalog = _CatalogGateway()
        self.client.cookies[SESSION_COOKIE_NAME] = "tok"

        with self._patch(session, catalog):
            response = self.client.get("/panel/catalog/products")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"], "servicio_no_disponible")
        self.assertEqual(catalog.calls, [])

    def test_catalog_client_error_is_proxied(self):
        session = _SessionGateway()
        catalog = _CatalogGateway(
            response=CatalogResponse(status_code=404, body={"error": "no_encontrado"})
        )
        self.client.cookies[SESSION_COOKIE_NAME] = "tok"

        with self._patch(session, catalog):
            response = self.client.delete("/panel/catalog/products/p1")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"error": "no_encontrado"})

    def test_catalog_server_error_is_503(self):
        session = _SessionGateway()
        catalog = _CatalogGateway(error=CatalogServiceUnavailable())
        self.client.cookies[SESSION_COOKIE_NAME] = "tok"

        with self._patch(session, catalog):
            response = self.client.get("/panel/catalog/products")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"], "servicio_no_disponible")

    def test_client_owner_is_ignored_and_session_owner_used(self):
        session = _SessionGateway()
        catalog = _CatalogGateway(response=CatalogResponse(status_code=200, body={"id": "p1"}))
        self.client.cookies[SESSION_COOKIE_NAME] = "tok"

        with self._patch(session, catalog):
            response = self.client.post(
                "/panel/catalog/products?ownerAccountId=intruso",
                data={"name": "camisa", "ownerAccountId": "intruso"},
                format="json",
            )

        self.assertEqual(response.status_code, 200)
        method, owner, _body, content_type = catalog.calls[0]
        self.assertEqual(method, "create_product")
        self.assertEqual(owner, "acc-session")
        self.assertEqual(content_type, "application/json")

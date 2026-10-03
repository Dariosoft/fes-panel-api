import unittest

from catalog.domain import SessionServiceUnavailable
from catalog.dtos import CatalogResponse, PanelSession
from catalog.use_cases import (
    create_product,
    delete_product,
    list_products,
    publish_catalog,
    publish_product,
    resolve_panel_owner,
    unpublish_product,
    update_product,
)


class _SessionGateway:
    def __init__(self, session: PanelSession | None = None, error: Exception | None = None):
        self._session = session
        self._error = error
        self.last_cookie = None

    def resolve(self, fes_session: str | None) -> PanelSession:
        self.last_cookie = fes_session
        if self._error:
            raise self._error
        return self._session


class ResolvePanelOwnerTests(unittest.TestCase):
    def test_authenticated_session_returns_account_id(self):
        gateway = _SessionGateway(PanelSession(authenticated=True, account_id="acc-1"))

        session = resolve_panel_owner(gateway, "cookie-value")

        self.assertTrue(session.authenticated)
        self.assertEqual(session.account_id, "acc-1")
        self.assertEqual(gateway.last_cookie, "cookie-value")

    def test_anonymous_session_is_not_reinterpreted(self):
        gateway = _SessionGateway(PanelSession(authenticated=False, account_id=None))

        session = resolve_panel_owner(gateway, None)

        self.assertFalse(session.authenticated)
        self.assertIsNone(session.account_id)

    def test_infrastructure_failure_becomes_unavailable(self):
        gateway = _SessionGateway(error=TimeoutError("boom"))

        with self.assertRaises(SessionServiceUnavailable):
            resolve_panel_owner(gateway, "x")

    def test_existing_unavailable_error_is_propagated(self):
        gateway = _SessionGateway(error=SessionServiceUnavailable())

        with self.assertRaises(SessionServiceUnavailable):
            resolve_panel_owner(gateway, "x")


class _CatalogGateway:
    def __init__(self, response: CatalogResponse | None = None):
        self._response = response or CatalogResponse(status_code=200, body={})
        self.calls: list[tuple] = []

    def list_products(self, owner_account_id: str, name: str | None = None) -> CatalogResponse:
        self.calls.append(("list_products", owner_account_id, name))
        return self._response

    def create_product(
        self, owner_account_id: str, body: bytes, content_type: str | None
    ) -> CatalogResponse:
        self.calls.append(("create_product", owner_account_id, body, content_type))
        return self._response

    def update_product(
        self,
        owner_account_id: str,
        product_id: str,
        body: bytes,
        content_type: str | None,
    ) -> CatalogResponse:
        self.calls.append(("update_product", owner_account_id, product_id, body, content_type))
        return self._response

    def delete_product(self, owner_account_id: str, product_id: str) -> CatalogResponse:
        self.calls.append(("delete_product", owner_account_id, product_id))
        return self._response

    def publish_product(self, owner_account_id: str, product_id: str) -> CatalogResponse:
        self.calls.append(("publish_product", owner_account_id, product_id))
        return self._response

    def unpublish_product(self, owner_account_id: str, product_id: str) -> CatalogResponse:
        self.calls.append(("unpublish_product", owner_account_id, product_id))
        return self._response

    def publish_catalog(
        self, owner_account_id: str, body: bytes, content_type: str | None
    ) -> CatalogResponse:
        self.calls.append(("publish_catalog", owner_account_id, body, content_type))
        return self._response


class ProductUseCasesTests(unittest.TestCase):
    def test_list_products_forwards_owner(self):
        gateway = _CatalogGateway()
        result = list_products(gateway, "acc-1")
        self.assertEqual(gateway.calls, [("list_products", "acc-1", None)])
        self.assertEqual(result.status_code, 200)

    def test_create_product_forwards_owner_and_body(self):
        gateway = _CatalogGateway()
        create_product(gateway, "acc-1", b'{"name":"camisa"}', "application/json")
        self.assertEqual(
            gateway.calls,
            [("create_product", "acc-1", b'{"name":"camisa"}', "application/json")],
        )

    def test_create_product_forwards_body_verbatim_and_session_owner(self):
        gateway = _CatalogGateway()
        body = b'{"ownerAccountId":"intruso","name":"camisa"}'

        create_product(gateway, "acc-session", body, "application/json")

        self.assertEqual(
            gateway.calls,
            [("create_product", "acc-session", body, "application/json")],
        )

    def test_update_product_forwards_owner_id_and_body(self):
        gateway = _CatalogGateway()
        update_product(gateway, "acc-1", "p9", b'{"name":"x"}', "multipart/form-data")
        self.assertEqual(
            gateway.calls,
            [("update_product", "acc-1", "p9", b'{"name":"x"}', "multipart/form-data")],
        )

    def test_delete_product_forwards_owner_and_id(self):
        gateway = _CatalogGateway()
        delete_product(gateway, "acc-1", "p9")
        self.assertEqual(gateway.calls, [("delete_product", "acc-1", "p9")])

    def test_publish_product_forwards_owner_and_id(self):
        gateway = _CatalogGateway()
        publish_product(gateway, "acc-1", "p9")
        self.assertEqual(gateway.calls, [("publish_product", "acc-1", "p9")])

    def test_unpublish_product_forwards_owner_and_id(self):
        gateway = _CatalogGateway()
        unpublish_product(gateway, "acc-1", "p9")
        self.assertEqual(gateway.calls, [("unpublish_product", "acc-1", "p9")])

    def test_publish_catalog_forwards_owner_and_body(self):
        gateway = _CatalogGateway()
        publish_catalog(gateway, "acc-1", b'{"products":[]}', "application/json")
        self.assertEqual(
            gateway.calls,
            [("publish_catalog", "acc-1", b'{"products":[]}', "application/json")],
        )

    def test_publish_catalog_zero_published_is_propagated(self):
        gateway = _CatalogGateway(response=CatalogResponse(status_code=200, body={"published": 0}))

        result = publish_catalog(gateway, "acc-1", b"{}", "application/json")

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.body, {"published": 0})

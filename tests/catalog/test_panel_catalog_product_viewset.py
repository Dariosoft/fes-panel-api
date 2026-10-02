from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase
from rest_framework.response import Response

from catalog.api.views import PanelCatalogProductViewSet
from catalog.domain import SESSION_COOKIE_NAME, CatalogServiceUnavailable
from catalog.dtos import CatalogResponse, PanelSession


class _SessionGateway:
    def resolve(self, fes_session: str | None) -> PanelSession:
        return PanelSession(authenticated=True, account_id="acc-1")


class _CatalogGateway:
    def __init__(self, response: CatalogResponse | None = None, error: Exception | None = None):
        self._response = response or CatalogResponse(status_code=200, body={"ok": True})
        self._error = error
        self.calls: list[tuple] = []

    def _record(self, *call) -> Response:
        self.calls.append(call)
        if self._error:
            raise self._error
        return self._response

    def list_products(self, owner_account_id, name=None):
        return self._record("list_products", owner_account_id, name)

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


class PanelCatalogProductViewSetTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.session_gateway = _SessionGateway()

    def _call(self, action: str, method: str, path: str, catalog_gateway, view_kwargs=None):
        view = PanelCatalogProductViewSet.as_view({method: action})
        request = getattr(self.factory, method)(
            path,
            HTTP_COOKIE=f"{SESSION_COOKIE_NAME}=tok",
        )
        with (
            patch.object(
                PanelCatalogProductViewSet, "_session_gateway", return_value=self.session_gateway
            ),
            patch.object(
                PanelCatalogProductViewSet, "_catalog_gateway", return_value=catalog_gateway
            ),
        ):
            return view(request, **(view_kwargs or {}))

    def test_list_forwards_owner(self):
        gateway = _CatalogGateway()

        response = self._call("list", "get", "/products", gateway)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(gateway.calls, [("list_products", "acc-1", None)])

    def test_list_forwards_name_filter(self):
        gateway = _CatalogGateway()
        view = PanelCatalogProductViewSet.as_view({"get": "list"})
        request = self.factory.get(
            "/products?name=mat",
            HTTP_COOKIE=f"{SESSION_COOKIE_NAME}=tok",
        )
        with (
            patch.object(
                PanelCatalogProductViewSet, "_session_gateway", return_value=self.session_gateway
            ),
            patch.object(PanelCatalogProductViewSet, "_catalog_gateway", return_value=gateway),
        ):
            response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(gateway.calls, [("list_products", "acc-1", "mat")])

    def test_create_forwards_owner_and_body(self):
        gateway = _CatalogGateway()
        view = PanelCatalogProductViewSet.as_view({"post": "create"})
        request = self.factory.post(
            "/products",
            data=b'{"name":"camisa"}',
            content_type="application/json",
            HTTP_COOKIE=f"{SESSION_COOKIE_NAME}=tok",
        )
        with (
            patch.object(
                PanelCatalogProductViewSet, "_session_gateway", return_value=self.session_gateway
            ),
            patch.object(PanelCatalogProductViewSet, "_catalog_gateway", return_value=gateway),
        ):
            response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            gateway.calls,
            [("create_product", "acc-1", b'{"name":"camisa"}', "application/json")],
        )

    def test_create_forwards_full_multipart_content_type(self):
        gateway = _CatalogGateway()
        view = PanelCatalogProductViewSet.as_view({"post": "create"})
        request = self.factory.post(
            "/products",
            data=b"--boundary\r\nContent-Disposition: form-data;\r\n\r\ncamisa\r\n--boundary--\r\n",
            content_type="multipart/form-data; boundary=boundary",
            HTTP_COOKIE=f"{SESSION_COOKIE_NAME}=tok",
        )
        with (
            patch.object(
                PanelCatalogProductViewSet, "_session_gateway", return_value=self.session_gateway
            ),
            patch.object(PanelCatalogProductViewSet, "_catalog_gateway", return_value=gateway),
        ):
            response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(gateway.calls[0][3], "multipart/form-data; boundary=boundary")

    def test_update_forwards_id_and_body(self):
        gateway = _CatalogGateway()
        view = PanelCatalogProductViewSet.as_view({"put": "update"})
        request = self.factory.put(
            "/products/p9",
            data=b'{"name":"x"}',
            content_type="application/json",
            HTTP_COOKIE=f"{SESSION_COOKIE_NAME}=tok",
        )
        with (
            patch.object(
                PanelCatalogProductViewSet, "_session_gateway", return_value=self.session_gateway
            ),
            patch.object(PanelCatalogProductViewSet, "_catalog_gateway", return_value=gateway),
        ):
            response = view(request, product_id="p9")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            gateway.calls,
            [("update_product", "acc-1", "p9", b'{"name":"x"}', "application/json")],
        )

    def test_destroy_forwards_id(self):
        gateway = _CatalogGateway()

        response = self._call("destroy", "delete", "/products/p9", gateway, {"product_id": "p9"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(gateway.calls, [("delete_product", "acc-1", "p9")])

    def test_publish_and_unpublish_forward_id(self):
        gateway = _CatalogGateway()

        self._call("publish", "post", "/products/p9/publish", gateway, {"product_id": "p9"})
        self._call("unpublish", "post", "/products/p9/unpublish", gateway, {"product_id": "p9"})

        self.assertEqual(
            gateway.calls,
            [("publish_product", "acc-1", "p9"), ("unpublish_product", "acc-1", "p9")],
        )

    def test_catalog_error_is_unavailable(self):
        gateway = _CatalogGateway(error=CatalogServiceUnavailable())

        response = self._call("list", "get", "/products", gateway)

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data["error"], "servicio_no_disponible")

    def test_client_error_is_proxied(self):
        gateway = _CatalogGateway(
            response=CatalogResponse(status_code=404, body={"error": "no_encontrado"})
        )

        response = self._call("destroy", "delete", "/products/p9", gateway, {"product_id": "p9"})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {"error": "no_encontrado"})

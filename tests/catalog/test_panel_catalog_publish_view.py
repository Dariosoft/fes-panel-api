from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase

from catalog.api.views import PanelCatalogPublishView
from common.contracts.account_api import SESSION_COOKIE_NAME
from common.dtos import AccountSession, ServiceResponse
from common.errors import CatalogApiUnavailable


class _SessionGateway:
    def __init__(self, authenticated=True, error=None):
        self._authenticated = authenticated
        self._error = error

    def get_session(self, fes_session: str | None) -> AccountSession:
        if self._error:
            raise self._error
        if not self._authenticated:
            return AccountSession(200, {}, False, None)
        return AccountSession(200, {}, True, "acc-1")


class _CatalogGateway:
    def __init__(self, response: ServiceResponse | None = None, error: Exception | None = None):
        self._response = response or ServiceResponse(status_code=200, body={"published": 0})
        self._error = error
        self.calls: list[tuple] = []

    def publish_catalog(self, owner_account_id, body, content_type):
        self.calls.append(("publish_catalog", owner_account_id, body, content_type))
        if self._error:
            raise self._error
        return self._response


class PanelCatalogPublishViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _post(self, catalog_gateway, session_gateway=None, cookie="tok"):
        request = self.factory.post(
            "/catalog/publish",
            data=b'{"products":[]}',
            content_type="application/json",
            HTTP_COOKIE=f"{SESSION_COOKIE_NAME}={cookie}" if cookie else "",
        )
        with (
            patch.object(
                PanelCatalogPublishView,
                "_session_gateway",
                return_value=session_gateway or _SessionGateway(),
            ),
            patch.object(PanelCatalogPublishView, "_catalog_gateway", return_value=catalog_gateway),
        ):
            return PanelCatalogPublishView.as_view()(request)

    def test_forwards_body_and_owner_and_propagates_count(self):
        gateway = _CatalogGateway(response=ServiceResponse(status_code=200, body={"published": 0}))

        response = self._post(gateway)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"published": 0})
        self.assertEqual(
            gateway.calls,
            [("publish_catalog", "acc-1", b'{"products":[]}', "application/json")],
        )

    def test_publish_defaults_to_json_when_body_is_absent(self):
        gateway = _CatalogGateway()
        request = self.factory.post(
            "/catalog/publish",
            data=b"",
            content_type="text/plain",
            HTTP_COOKIE=f"{SESSION_COOKIE_NAME}=tok",
        )
        request.META["CONTENT_TYPE"] = ""
        with (
            patch.object(
                PanelCatalogPublishView, "_session_gateway", return_value=_SessionGateway()
            ),
            patch.object(PanelCatalogPublishView, "_catalog_gateway", return_value=gateway),
        ):
            response = PanelCatalogPublishView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(gateway.calls, [("publish_catalog", "acc-1", b"{}", "application/json")])

    def test_missing_session_is_unauthorized_and_does_not_forward(self):
        gateway = _CatalogGateway()

        response = self._post(
            gateway, session_gateway=_SessionGateway(authenticated=False), cookie=None
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["error"], "no_autenticado")
        self.assertEqual(gateway.calls, [])

    def test_catalog_error_is_unavailable(self):
        gateway = _CatalogGateway(error=CatalogApiUnavailable())

        response = self._post(gateway)

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data["error"], "servicio_no_disponible")

from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase

from catalog.api.views import PanelCatalogPublishView
from catalog.domain import SESSION_COOKIE_NAME, CatalogServiceUnavailable
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
        return PanelSession(authenticated=True, account_id="acc-1")


class _CatalogGateway:
    def __init__(self, response: CatalogResponse | None = None, error: Exception | None = None):
        self._response = response or CatalogResponse(status_code=200, body={"published": 0})
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
        gateway = _CatalogGateway(response=CatalogResponse(status_code=200, body={"published": 0}))

        response = self._post(gateway)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"published": 0})
        self.assertEqual(
            gateway.calls,
            [("publish_catalog", "acc-1", b'{"products":[]}', "application/json")],
        )

    def test_missing_session_is_unauthorized_and_does_not_forward(self):
        gateway = _CatalogGateway()

        response = self._post(
            gateway, session_gateway=_SessionGateway(authenticated=False), cookie=None
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["error"], "no_autenticado")
        self.assertEqual(gateway.calls, [])

    def test_catalog_error_is_unavailable(self):
        gateway = _CatalogGateway(error=CatalogServiceUnavailable())

        response = self._post(gateway)

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data["error"], "servicio_no_disponible")

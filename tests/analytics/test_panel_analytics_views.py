from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.test import APIClient

from common.contracts.account_api import SESSION_COOKIE_NAME
from common.dtos import AccountSession, ServiceResponse
from common.errors import (
    AccountApiUnavailable,
    AnalyticsApiTimeout,
    AnalyticsApiUnavailable,
)


class _SessionGateway:
    def __init__(self, session: AccountSession | None = None, error: Exception | None = None):
        self._session = session
        self._error = error

    def get_session(self, fes_session: str | None) -> AccountSession:
        if self._error:
            raise self._error
        return self._session


class _AnalyticsGateway:
    def __init__(self, response: ServiceResponse | None = None, error: Exception | None = None):
        self._response = response or ServiceResponse(status_code=200, body={"ok": True})
        self._error = error
        self.calls: list[tuple] = []

    def timeline(self, tenant_id: str, order_id: str | None = None) -> ServiceResponse:
        self.calls.append(("timeline", tenant_id, order_id))
        if self._error:
            raise self._error
        return self._response

    def metrics(self, tenant_id: str) -> ServiceResponse:
        self.calls.append(("metrics", tenant_id))
        if self._error:
            raise self._error
        return self._response


class PanelAnalyticsViewTests(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.cookies[SESSION_COOKIE_NAME] = "tok"

    def _run(self, path, analytics, session=None):
        session = session or _SessionGateway(AccountSession(200, {}, True, "tenant-1"))
        with patch.multiple(
            "analytics.api.panel_session",
            build_account_api_gateway=lambda: session,
            build_analytics_api_gateway=lambda: analytics,
        ):
            return self.client.get(path)

    def test_timeline_forwards_resolved_tenant_and_order(self):
        analytics = _AnalyticsGateway(
            ServiceResponse(status_code=200, body={"events": [{"id": "e1"}]})
        )

        response = self._run("/panel/analytics/timeline?orderId=order-9", analytics)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"events": [{"id": "e1"}]})
        self.assertEqual(analytics.calls, [("timeline", "tenant-1", "order-9")])

    def test_metrics_forwards_resolved_tenant(self):
        analytics = _AnalyticsGateway(ServiceResponse(status_code=200, body={"orders": 2}))

        response = self._run("/panel/analytics/metrics", analytics)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"orders": 2})
        self.assertEqual(analytics.calls, [("metrics", "tenant-1")])

    def test_upstream_failure_returns_502_without_details(self):
        analytics = _AnalyticsGateway(error=AnalyticsApiUnavailable())

        response = self._run("/panel/analytics/metrics", analytics)

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["error"], "servicio_no_disponible")

    def test_upstream_timeout_returns_504(self):
        analytics = _AnalyticsGateway(error=AnalyticsApiTimeout())

        response = self._run("/panel/analytics/timeline", analytics)

        self.assertEqual(response.status_code, 504)
        self.assertEqual(response.json()["error"], "tiempo_de_espera_agotado")

    def test_unauthenticated_session_returns_401(self):
        session = _SessionGateway(AccountSession(200, {}, False, None))

        response = self._run("/panel/analytics/metrics", _AnalyticsGateway(), session)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"], "no_autenticado")

    def test_account_service_failure_returns_503(self):
        session = _SessionGateway(error=AccountApiUnavailable())

        response = self._run("/panel/analytics/metrics", _AnalyticsGateway(), session)

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"], "servicio_no_disponible")

import unittest

from analytics.use_cases import get_metrics, get_timeline, resolve_panel_tenant
from common.dtos import AccountSession, ServiceResponse
from common.errors import AccountApiUnavailable


class _SessionGateway:
    def __init__(self, session: AccountSession | None = None, error: Exception | None = None):
        self._session = session
        self._error = error
        self.last_cookie = None

    def get_session(self, fes_session: str | None) -> AccountSession:
        self.last_cookie = fes_session
        if self._error:
            raise self._error
        return self._session


class _AnalyticsGateway:
    def __init__(self, response: ServiceResponse | None = None):
        self._response = response or ServiceResponse(status_code=200, body={})
        self.calls: list[tuple] = []

    def timeline(self, tenant_id: str, order_id: str | None = None) -> ServiceResponse:
        self.calls.append(("timeline", tenant_id, order_id))
        return self._response

    def metrics(self, tenant_id: str) -> ServiceResponse:
        self.calls.append(("metrics", tenant_id))
        return self._response


class ResolvePanelTenantTests(unittest.TestCase):
    def test_authenticated_session_returns_account_id(self):
        gateway = _SessionGateway(AccountSession(200, {}, True, "tenant-1"))

        tenant_id = resolve_panel_tenant(gateway, "cookie")

        self.assertEqual(tenant_id, "tenant-1")
        self.assertEqual(gateway.last_cookie, "cookie")

    def test_anonymous_session_returns_none(self):
        gateway = _SessionGateway(AccountSession(200, {}, False, None))

        self.assertIsNone(resolve_panel_tenant(gateway, None))

    def test_authenticated_session_without_id_returns_none(self):
        gateway = _SessionGateway(AccountSession(200, {}, True, None))

        self.assertIsNone(resolve_panel_tenant(gateway, "cookie"))

    def test_infrastructure_failure_becomes_unavailable(self):
        gateway = _SessionGateway(error=RuntimeError("boom"))

        with self.assertRaises(AccountApiUnavailable):
            resolve_panel_tenant(gateway, "cookie")

    def test_existing_unavailable_error_is_propagated(self):
        gateway = _SessionGateway(error=AccountApiUnavailable())

        with self.assertRaises(AccountApiUnavailable):
            resolve_panel_tenant(gateway, "cookie")


class AnalyticsUseCaseTests(unittest.TestCase):
    def test_get_timeline_forwards_tenant_and_order(self):
        gateway = _AnalyticsGateway(ServiceResponse(status_code=200, body={"events": []}))

        result = get_timeline(gateway, "tenant-1", "order-9")

        self.assertEqual(gateway.calls, [("timeline", "tenant-1", "order-9")])
        self.assertEqual(result.body, {"events": []})

    def test_get_metrics_forwards_tenant(self):
        gateway = _AnalyticsGateway(ServiceResponse(status_code=200, body={"orders": 1}))

        result = get_metrics(gateway, "tenant-1")

        self.assertEqual(gateway.calls, [("metrics", "tenant-1")])
        self.assertEqual(result.body, {"orders": 1})

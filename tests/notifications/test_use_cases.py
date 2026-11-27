import unittest
from typing import IO

from common.dtos import AccountSession
from common.errors import AccountApiUnavailable
from notifications.use_cases import open_feed, resolve_panel_tenant


class _SessionGateway:
    def __init__(self, session: AccountSession | None = None, error: Exception | None = None):
        self._session = session
        self._error = error

    def get_session(self, fes_session: str | None) -> AccountSession:
        if self._error:
            raise self._error
        return self._session


class _NotificationsGateway:
    def __init__(self, upstream: IO[bytes] | None = None):
        self._upstream = upstream
        self.calls: list[tuple] = []

    def open_feed(self, tenant_id: str) -> IO[bytes]:
        self.calls.append(("open_feed", tenant_id))
        return self._upstream


class ResolvePanelTenantTests(unittest.TestCase):
    def test_authenticated_session_returns_account_id(self):
        gateway = _SessionGateway(AccountSession(200, {}, True, "tenant-1"))

        self.assertEqual(resolve_panel_tenant(gateway, "cookie"), "tenant-1")

    def test_anonymous_session_returns_none(self):
        gateway = _SessionGateway(AccountSession(200, {}, False, None))

        self.assertIsNone(resolve_panel_tenant(gateway, None))

    def test_infrastructure_failure_becomes_unavailable(self):
        gateway = _SessionGateway(error=RuntimeError("boom"))

        with self.assertRaises(AccountApiUnavailable):
            resolve_panel_tenant(gateway, "cookie")

    def test_existing_unavailable_error_is_propagated(self):
        gateway = _SessionGateway(error=AccountApiUnavailable())

        with self.assertRaises(AccountApiUnavailable):
            resolve_panel_tenant(gateway, "cookie")


class OpenFeedUseCaseTests(unittest.TestCase):
    def test_open_feed_forwards_tenant(self):
        upstream = object()
        gateway = _NotificationsGateway(upstream)

        result = open_feed(gateway, "tenant-1")

        self.assertIs(result, upstream)
        self.assertEqual(gateway.calls, [("open_feed", "tenant-1")])

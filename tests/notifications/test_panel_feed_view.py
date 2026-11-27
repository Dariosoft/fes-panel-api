from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.test import APIClient

from common.contracts.account_api import SESSION_COOKIE_NAME
from common.dtos import AccountSession
from common.errors import (
    AccountApiUnavailable,
    NotificationsApiTimeout,
    NotificationsApiUnavailable,
)


class _SessionGateway:
    def __init__(self, session: AccountSession | None = None, error: Exception | None = None):
        self._session = session
        self._error = error

    def get_session(self, fes_session: str | None) -> AccountSession:
        if self._error:
            raise self._error
        return self._session


class _Upstream:
    def __init__(self, chunks: list[bytes]):
        self._chunks = list(chunks)
        self.closed = False

    def read(self, size: int = -1) -> bytes:
        if self._chunks:
            return self._chunks.pop(0)
        return b""

    def close(self) -> None:
        self.closed = True


class _NotificationsGateway:
    def __init__(self, upstream: _Upstream | None = None, error: Exception | None = None):
        self._upstream = upstream
        self._error = error
        self.calls: list[tuple] = []

    def open_feed(self, tenant_id: str):
        self.calls.append(("open_feed", tenant_id))
        if self._error:
            raise self._error
        return self._upstream


class PanelFeedViewTests(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.cookies[SESSION_COOKIE_NAME] = "tok"

    def _run(self, notifications, session=None):
        session = session or _SessionGateway(AccountSession(200, {}, True, "tenant-1"))
        with patch.multiple(
            "notifications.api.panel_session",
            build_account_api_gateway=lambda: session,
            build_notifications_api_gateway=lambda: notifications,
        ):
            return self.client.get("/panel/notifications/feed")

    def test_feed_streams_upstream_with_sse_headers(self):
        upstream = _Upstream([b"data: one\n\n", b"data: two\n\n"])
        notifications = _NotificationsGateway(upstream)

        response = self._run(notifications)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/event-stream")
        self.assertEqual(response["Cache-Control"], "no-cache")
        self.assertEqual(response["X-Accel-Buffering"], "no")
        self.assertEqual(notifications.calls, [("open_feed", "tenant-1")])
        self.assertEqual(b"".join(response.streaming_content), b"data: one\n\ndata: two\n\n")
        self.assertTrue(upstream.closed)

    def test_upstream_failure_returns_502_without_details(self):
        notifications = _NotificationsGateway(error=NotificationsApiUnavailable())

        response = self._run(notifications)

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["error"], "servicio_no_disponible")

    def test_upstream_timeout_returns_504(self):
        notifications = _NotificationsGateway(error=NotificationsApiTimeout())

        response = self._run(notifications)

        self.assertEqual(response.status_code, 504)
        self.assertEqual(response.json()["error"], "tiempo_de_espera_agotado")

    def test_unauthenticated_session_returns_401(self):
        session = _SessionGateway(AccountSession(200, {}, False, None))

        response = self._run(_NotificationsGateway(), session)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"], "no_autenticado")

    def test_account_service_failure_returns_503(self):
        session = _SessionGateway(error=AccountApiUnavailable())

        response = self._run(_NotificationsGateway(), session)

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"], "servicio_no_disponible")

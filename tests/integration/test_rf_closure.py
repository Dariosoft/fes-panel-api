import inspect
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from django.apps import apps
from django.test import SimpleTestCase, override_settings
from django.urls import resolve
from rest_framework.permissions import AllowAny
from rest_framework.test import APIClient

from common.health.views import live, ready
from identity.api.views import GoogleLoginRedirectView, PanelSessionViewSet
from identity.domain import SESSION_COOKIE_NAME
from identity.infrastructure.account_session_client import AccountSessionClient


class _AccountsHandler(BaseHTTPRequestHandler):
    session_body = {"authenticated": False}
    session_status = 200
    logout_body = {"authenticated": False}
    logout_status = 200
    last_cookie = None
    last_path = None

    def log_message(self, *args) -> None:
        return

    def do_GET(self) -> None:
        _AccountsHandler.last_path = self.path
        _AccountsHandler.last_cookie = self.headers.get("Cookie")
        payload = json.dumps(_AccountsHandler.session_body).encode("utf-8")
        self.send_response(_AccountsHandler.session_status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self) -> None:
        _AccountsHandler.last_path = self.path
        _AccountsHandler.last_cookie = self.headers.get("Cookie")
        payload = json.dumps(_AccountsHandler.logout_body).encode("utf-8")
        self.send_response(_AccountsHandler.logout_status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class LiveAccountsServerMixin:
    def start_accounts_server(self):
        _AccountsHandler.session_body = {"authenticated": False}
        _AccountsHandler.session_status = 200
        _AccountsHandler.logout_body = {"authenticated": False}
        _AccountsHandler.logout_status = 200
        _AccountsHandler.last_cookie = None
        _AccountsHandler.last_path = None
        self._server = HTTPServer(("127.0.0.1", 0), _AccountsHandler)
        self._port = self._server.server_address[1]
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        self.accounts_base = f"http://127.0.0.1:{self._port}"
        self._server_stopped = False

    def stop_accounts_server(self):
        if getattr(self, "_server_stopped", True):
            return
        self._server.shutdown()
        self._server.server_close()
        self._server_stopped = True


@override_settings(PANEL_PUBLIC_ORIGIN="https://panel.example.com")
class RedirectAndBaseUrlTests(LiveAccountsServerMixin, SimpleTestCase):
    def setUp(self):
        self.client = APIClient()
        self.start_accounts_server()

    def tearDown(self):
        self.stop_accounts_server()

    def test_login_redirect_uses_return_to_and_account_base(self):
        with override_settings(
            ACCOUNT_API_BASE_URL=self.accounts_base,
            ACCOUNTS_PUBLIC_BASE_URL=self.accounts_base,
        ):
            response = self.client.get("/panel/login/google")
        self.assertIn(response.status_code, (302, 303))
        parsed = urlparse(response["Location"])
        self.assertEqual(parsed.netloc, f"127.0.0.1:{self._port}")
        self.assertEqual(parsed.path, "/accounts/login/google")
        self.assertEqual(parse_qs(parsed.query)["return_to"], ["https://panel.example.com"])

    def test_session_client_uses_account_api_base_url(self):
        _AccountsHandler.session_body = {
            "authenticated": True,
            "id": "1",
            "email": "a@b.c",
            "name": "A",
        }
        client = AccountSessionClient(self.accounts_base, timeout_seconds=2)
        result = client.get_session("cookie")
        self.assertEqual(_AccountsHandler.last_path, "/accounts/session")
        self.assertEqual(result.body["authenticated"], True)


@override_settings(PANEL_PUBLIC_ORIGIN="https://panel.example.com")
class SessionIntegrationTests(LiveAccountsServerMixin, SimpleTestCase):
    def setUp(self):
        self.client = APIClient()
        self.start_accounts_server()

    def tearDown(self):
        self.stop_accounts_server()

    def test_session_proxy_identical_json(self):
        body = {"authenticated": True, "id": "9", "email": "x@y.z", "name": "X"}
        _AccountsHandler.session_body = body
        with override_settings(ACCOUNT_API_BASE_URL=self.accounts_base):
            self.client.cookies[SESSION_COOKIE_NAME] = "sess"
            response = self.client.get("/panel/session")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), body)
        self.assertEqual(_AccountsHandler.last_cookie, f"{SESSION_COOKIE_NAME}=sess")

    def test_session_invalid_is_anonymous_json(self):
        _AccountsHandler.session_body = {"authenticated": False}
        with override_settings(ACCOUNT_API_BASE_URL=self.accounts_base):
            self.client.cookies[SESSION_COOKIE_NAME] = "bad"
            response = self.client.get("/panel/session")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"authenticated": False})

    def test_session_down_returns_503_distinct_body(self):
        self.stop_accounts_server()
        with override_settings(
            ACCOUNT_API_BASE_URL=self.accounts_base,
            ACCOUNT_API_TIMEOUT_SECONDS=0.5,
        ):
            response = self.client.get("/panel/session")
        self.assertEqual(response.status_code, 503)
        self.assertNotEqual(response.json(), {"authenticated": False})
        self.assertIn("message", response.json())


@override_settings(PANEL_PUBLIC_ORIGIN="https://panel.example.com")
class LogoutIntegrationTests(LiveAccountsServerMixin, SimpleTestCase):
    def setUp(self):
        self.client = APIClient()
        self.start_accounts_server()

    def tearDown(self):
        self.stop_accounts_server()

    def test_logout_ok_calls_accounts_and_clears_cookie(self):
        with override_settings(ACCOUNT_API_BASE_URL=self.accounts_base):
            self.client.cookies[SESSION_COOKIE_NAME] = "sess"
            response = self.client.delete("/panel/session")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(_AccountsHandler.last_path, "/accounts/logout")
        self.assertEqual(_AccountsHandler.last_cookie, f"{SESSION_COOKIE_NAME}=sess")
        self.assertEqual(response.cookies[SESSION_COOKIE_NAME]["max-age"], 0)

    def test_logout_without_session_is_idempotent(self):
        with override_settings(ACCOUNT_API_BASE_URL=self.accounts_base):
            response = self.client.delete("/panel/session")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["authenticated"])
        self.assertEqual(response.cookies[SESSION_COOKIE_NAME]["max-age"], 0)

    def test_logout_failure_does_not_clear_cookie(self):
        self.stop_accounts_server()
        with override_settings(
            ACCOUNT_API_BASE_URL=self.accounts_base,
            ACCOUNT_API_TIMEOUT_SECONDS=0.5,
        ):
            self.client.cookies[SESSION_COOKIE_NAME] = "sess"
            response = self.client.delete("/panel/session")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(SESSION_COOKIE_NAME, response.cookies)


class RfCoverageSmokeTests(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()

    def test_identity_has_no_account_model_or_migrations(self):
        identity_app = apps.get_app_config("identity")
        self.assertEqual(list(identity_app.get_models()), [])
        migrations_dir = Path(identity_app.path) / "migrations"
        self.assertFalse(migrations_dir.exists())

    def test_endpoints_are_allow_any(self):
        for view in (GoogleLoginRedirectView, PanelSessionViewSet):
            self.assertIn(AllowAny, view.permission_classes)

    def test_session_and_logout_do_not_import_shops(self):
        import identity.api.views as views_module

        source = inspect.getsource(views_module)
        self.assertNotIn("shops", source)

    @override_settings(
        PANEL_PUBLIC_ORIGIN="https://panel.example.com",
        CORS_ALLOWED_ORIGINS=["https://panel.example.com"],
        CORS_ALLOW_CREDENTIALS=True,
    )
    def test_cors_preflight_allows_panel_origin_with_credentials(self):
        response = self.client.options(
            "/panel/session",
            HTTP_ORIGIN="https://panel.example.com",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Access-Control-Allow-Origin"], "https://panel.example.com")
        self.assertEqual(response["Access-Control-Allow-Credentials"], "true")

    def test_health_smoke(self):
        self.assertEqual(resolve("/health/live").func, live)
        self.assertEqual(resolve("/health/ready").func, ready)
        live_response = self.client.get("/health/live")
        self.assertEqual(live_response.status_code, 200)
        self.assertEqual(live_response.json(), {"status": "live"})

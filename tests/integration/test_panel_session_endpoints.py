from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIClient

from common.health.views import live, ready
from common.panel.views import panel
from identity.application.dtos import LogoutResult, SessionPayload
from identity.domain import SESSION_COOKIE_NAME, AccountServiceUnavailable


class _FakeGateway:
    def __init__(
        self,
        session_payload=None,
        logout_result=None,
        session_error=None,
        logout_error=None,
    ):
        self.session_payload = session_payload
        self.logout_result = logout_result
        self.session_error = session_error
        self.logout_error = logout_error
        self.last_session_cookie = None
        self.last_logout_cookie = None

    def get_session(self, fes_session):
        self.last_session_cookie = fes_session
        if self.session_error:
            raise self.session_error
        return self.session_payload

    def logout(self, fes_session):
        self.last_logout_cookie = fes_session
        if self.logout_error:
            raise self.logout_error
        return self.logout_result


@override_settings(
    ACCOUNT_API_BASE_URL="http://account-api.test:8080",
    ACCOUNTS_PUBLIC_BASE_URL="http://account-api.test:8080",
    PANEL_PUBLIC_ORIGIN="https://panel.example.com",
)
class PanelIdentityEndpointTests(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()

    def test_google_login_redirects_with_return_to(self):
        response = self.client.get("/panel/login/google")
        self.assertIn(response.status_code, (302, 303))
        location = response["Location"]
        parsed = urlparse(location)
        self.assertEqual(parsed.netloc, "account-api.test:8080")
        self.assertEqual(parsed.path, "/accounts/login/google")
        self.assertEqual(parse_qs(parsed.query)["return_to"], ["https://panel.example.com"])

    @override_settings(
        ACCOUNT_API_BASE_URL="http://account-api.apps.svc.cluster.local:8080",
        ACCOUNTS_PUBLIC_BASE_URL="https://api.example.com",
        PANEL_PUBLIC_ORIGIN="https://panel.example.com",
    )
    def test_google_login_redirects_the_browser_to_the_public_api(self):
        response = self.client.get("/panel/login/google")
        parsed = urlparse(response["Location"])
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.netloc, "api.example.com")
        self.assertEqual(parsed.path, "/accounts/login/google")

    def test_session_proxies_payload(self):
        payload = SessionPayload(
            status_code=200,
            body={"authenticated": True, "id": "1", "email": "a@b.c", "name": "A"},
        )
        gateway = _FakeGateway(session_payload=payload)
        with patch("identity.api.views._gateway", return_value=gateway):
            self.client.cookies[SESSION_COOKIE_NAME] = "tok"
            response = self.client.get("/panel/session")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), payload.body)
        self.assertEqual(gateway.last_session_cookie, "tok")

    def test_session_anonymous(self):
        payload = SessionPayload(status_code=200, body={"authenticated": False})
        gateway = _FakeGateway(session_payload=payload)
        with patch("identity.api.views._gateway", return_value=gateway):
            response = self.client.get("/panel/session")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"authenticated": False})

    def test_session_unavailable_is_503_distinct_shape(self):
        gateway = _FakeGateway(session_error=AccountServiceUnavailable())
        with patch("identity.api.views._gateway", return_value=gateway):
            response = self.client.get("/panel/session")
        self.assertEqual(response.status_code, 503)
        body = response.json()
        self.assertNotEqual(body, {"authenticated": False})
        self.assertIn("message", body)

    def test_logout_clears_cookie(self):
        result = LogoutResult(
            status_code=200,
            body={"authenticated": False},
            had_active_session=True,
        )
        gateway = _FakeGateway(logout_result=result)
        with patch("identity.api.views._gateway", return_value=gateway):
            self.client.cookies[SESSION_COOKIE_NAME] = "tok"
            response = self.client.post("/panel/logout")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"authenticated": False})
        self.assertEqual(gateway.last_logout_cookie, "tok")
        self.assertIn(SESSION_COOKIE_NAME, response.cookies)
        self.assertEqual(response.cookies[SESSION_COOKIE_NAME]["max-age"], 0)

    def test_logout_without_session_clears_cookie(self):
        result = LogoutResult(
            status_code=200,
            body={"authenticated": False},
            had_active_session=False,
        )
        gateway = _FakeGateway(logout_result=result)
        with patch("identity.api.views._gateway", return_value=gateway):
            response = self.client.post("/panel/logout")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["authenticated"])
        self.assertEqual(response.cookies[SESSION_COOKIE_NAME]["max-age"], 0)

    def test_logout_unavailable_keeps_cookie(self):
        gateway = _FakeGateway(logout_error=AccountServiceUnavailable())
        with patch("identity.api.views._gateway", return_value=gateway):
            self.client.cookies[SESSION_COOKIE_NAME] = "tok"
            response = self.client.post("/panel/logout")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(SESSION_COOKIE_NAME, response.cookies)
        self.assertNotEqual(response.json(), {"authenticated": False})

    def test_existing_routes_resolve(self):
        from django.urls import resolve

        self.assertEqual(resolve("/panel").func, panel)
        self.assertEqual(resolve("/health/live").func, live)
        self.assertEqual(resolve("/health/ready").func, ready)

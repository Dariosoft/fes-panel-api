import unittest
from urllib.parse import parse_qs, urlparse

from common.dtos import AccountLogout, AccountSession
from common.errors import AccountApiUnavailable
from identity.navigation import build_google_login_redirect_url
from identity.use_cases import logout_panel_session, resolve_panel_session


class BuildGoogleLoginRedirectTests(unittest.TestCase):
    def test_return_to_is_panel_public_origin(self):
        url = build_google_login_redirect_url(
            "http://account-api.internal:8080/",
            "https://panel.example.com",
        )
        parsed = urlparse(url)
        self.assertEqual(parsed.scheme, "http")
        self.assertEqual(parsed.netloc, "account-api.internal:8080")
        self.assertEqual(parsed.path, "/accounts/login/google")
        self.assertEqual(parse_qs(parsed.query)["return_to"], ["https://panel.example.com"])

    def test_return_to_appends_the_requested_path(self):
        url = build_google_login_redirect_url(
            "http://account-api.internal:8080/",
            "https://panel.example.com",
            "/catalog?page=1",
        )
        parsed = urlparse(url)
        self.assertEqual(
            parse_qs(parsed.query)["return_to"],
            ["https://panel.example.com/catalog?page=1"],
        )

    def test_unsafe_return_to_falls_back_to_the_origin(self):
        for unsafe in ("//evil.example", "https://evil.example/catalog", "catalog"):
            url = build_google_login_redirect_url(
                "http://account-api.internal:8080",
                "https://panel.example.com",
                unsafe,
            )
            parsed = urlparse(url)
            self.assertEqual(
                parse_qs(parsed.query)["return_to"],
                ["https://panel.example.com"],
            )


class ResolvePanelSessionTests(unittest.TestCase):
    def test_success_propagates_payload(self):
        payload = AccountSession(
            status_code=200,
            body={"authenticated": True, "id": "u1", "email": "a@b.c", "name": "A"},
            authenticated=True,
            account_id="u1",
        )

        class Gateway:
            def get_session(self, fes_session: str | None) -> AccountSession:
                self.cookie = fes_session
                return payload

            def logout(self, fes_session: str | None) -> AccountLogout:
                raise AssertionError("logout should not be called")

        gateway = Gateway()
        result = resolve_panel_session(gateway, "cookie-value")
        self.assertIs(result, payload)
        self.assertEqual(gateway.cookie, "cookie-value")

    def test_anonymous_payload_propagated_unchanged(self):
        payload = AccountSession(200, {"authenticated": False}, False, None)

        class Gateway:
            def get_session(self, fes_session: str | None) -> AccountSession:
                return payload

            def logout(self, fes_session: str | None) -> AccountLogout:
                raise AssertionError("logout should not be called")

        result = resolve_panel_session(Gateway(), None)
        self.assertEqual(result.body, {"authenticated": False})

    def test_infrastructure_failure_becomes_unavailable(self):
        class Gateway:
            def get_session(self, fes_session: str | None) -> AccountSession:
                raise TimeoutError("boom")

            def logout(self, fes_session: str | None) -> AccountLogout:
                raise AssertionError("logout should not be called")

        with self.assertRaises(AccountApiUnavailable):
            resolve_panel_session(Gateway(), "x")


class LogoutPanelSessionTests(unittest.TestCase):
    def test_success_clears_cookie(self):
        class Gateway:
            def get_session(self, fes_session: str | None) -> AccountSession:
                raise AssertionError("get_session should not be called")

            def logout(self, fes_session: str | None) -> AccountLogout:
                return AccountLogout(
                    status_code=200,
                    body={"authenticated": False},
                    had_active_session=True,
                )

        result = logout_panel_session(Gateway(), "cookie")
        self.assertTrue(result.clear_cookie)
        self.assertEqual(result.body, {"authenticated": False})

    def test_no_session_clears_cookie(self):
        class Gateway:
            def get_session(self, fes_session: str | None) -> AccountSession:
                raise AssertionError("get_session should not be called")

            def logout(self, fes_session: str | None) -> AccountLogout:
                return AccountLogout(
                    status_code=200,
                    body={"authenticated": False},
                    had_active_session=False,
                )

        result = logout_panel_session(Gateway(), None)
        self.assertTrue(result.clear_cookie)
        self.assertFalse(result.body["authenticated"])

    def test_failure_does_not_clear_cookie(self):
        class Gateway:
            def get_session(self, fes_session: str | None) -> AccountSession:
                raise AssertionError("get_session should not be called")

            def logout(self, fes_session: str | None) -> AccountLogout:
                raise AccountApiUnavailable("down")

        with self.assertRaises(AccountApiUnavailable):
            logout_panel_session(Gateway(), "cookie")

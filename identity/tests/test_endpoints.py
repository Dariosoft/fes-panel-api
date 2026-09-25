from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from identity.account_client import SESSION_COOKIE_NAME
from identity.services import LoginResult, WhoAmIResult
from identity.views import LoginView, LogoutView, WhoAmIView


class WhoAmIEndpointTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.service = MagicMock()

    def test_rf1_rf8_whoami_anonymous_without_session(self):
        """RF-1, RF-8: without session, response is unauthenticated with no invented identity."""
        self.service.whoami.return_value = WhoAmIResult(authenticated=False)
        request = self.factory.get("/panel/me")
        with patch("identity.views.get_identity_service", return_value=self.service):
            response = WhoAmIView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"authenticated": False})
        self.assertNotIn("name", response.data)
        self.assertNotIn("email", response.data)
        self.service.whoami.assert_called_once_with(None)

    def test_rf8_rf13_whoami_authenticated_with_session(self):
        """RF-8, RF-13: with shared session, return Google name and email."""
        self.service.whoami.return_value = WhoAmIResult(
            authenticated=True,
            name="Ada Lovelace",
            email="ada@example.com",
        )
        request = self.factory.get("/panel/me")
        request.COOKIES[SESSION_COOKIE_NAME] = "sess-1"
        with patch("identity.views.get_identity_service", return_value=self.service):
            response = WhoAmIView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                "authenticated": True,
                "name": "Ada Lovelace",
                "email": "ada@example.com",
            },
        )
        self.service.whoami.assert_called_once_with("sess-1")


class LogoutEndpointTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.service = MagicMock()

    def test_rf6_rf13_logout_authenticated_closes_shared_session(self):
        """RF-6, RF-13: logout closes shared session; whoami becomes anonymous."""
        request = self.factory.post("/panel/session/logout")
        request.COOKIES[SESSION_COOKIE_NAME] = "sess-1"
        with patch("identity.views.get_identity_service", return_value=self.service):
            response = LogoutView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"authenticated": False})
        self.service.logout.assert_called_once_with("sess-1")
        self.assertTrue(
            response.cookies[SESSION_COOKIE_NAME]["max-age"] == 0
            or response.cookies[SESSION_COOKIE_NAME].value == ""
        )

        self.service.whoami.return_value = WhoAmIResult(authenticated=False)
        whoami_request = self.factory.get("/panel/me")
        with patch("identity.views.get_identity_service", return_value=self.service):
            whoami = WhoAmIView.as_view()(whoami_request)
        self.assertEqual(whoami.data, {"authenticated": False})

    def test_rf10_logout_without_session_is_idempotent(self):
        """RF-10: anonymous logout succeeds and remains unauthenticated."""
        request = self.factory.post("/panel/session/logout")
        with patch("identity.views.get_identity_service", return_value=self.service):
            response = LogoutView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"authenticated": False})
        self.service.logout.assert_called_once_with(None)

        self.service.whoami.return_value = WhoAmIResult(authenticated=False)
        whoami_request = self.factory.get("/panel/me")
        with patch("identity.views.get_identity_service", return_value=self.service):
            whoami = WhoAmIView.as_view()(whoami_request)
        self.assertEqual(whoami.data, {"authenticated": False})


class LoginEndpointTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.service = MagicMock()

    def test_rf4_rejects_non_google_provider(self):
        """RF-4: only Google is accepted for panel login."""
        request = self.factory.post(
            "/panel/session/google",
            {"provider": "github", "credential": "token"},
            format="json",
        )
        with patch("identity.views.get_identity_service", return_value=self.service):
            response = LoginView.as_view()(request)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["authenticated"])
        self.assertIn("Google", response.data["message"])
        self.service.login_with_google.assert_not_called()

    def test_rf2_rf5_login_success_opens_shared_session(self):
        """RF-2, RF-5: confirmed Google access authenticates without local account writes."""
        self.service.login_with_google.return_value = LoginResult(
            authenticated=True,
            name="Ada Lovelace",
            email="ada@example.com",
            session_id="sess-1",
        )
        request = self.factory.post(
            "/panel/session/google",
            {"provider": "google", "credential": "google-credential"},
            format="json",
        )
        with (
            patch("identity.views.get_identity_service", return_value=self.service),
            patch("django.contrib.auth.models.User.objects") as user_objects,
            patch("shops.models.Shop.objects") as shop_objects,
        ):
            response = LoginView.as_view()(request)
            user_objects.create.assert_not_called()
            shop_objects.create.assert_not_called()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                "authenticated": True,
                "name": "Ada Lovelace",
                "email": "ada@example.com",
            },
        )
        self.assertEqual(response.cookies[SESSION_COOKIE_NAME].value, "sess-1")
        self.service.login_with_google.assert_called_once_with("google-credential")

    def test_rf3_login_without_panel_membership(self):
        """RF-3: recognized account may enter without Shop/membership in panel."""
        self.service.login_with_google.return_value = LoginResult(
            authenticated=True,
            name="Grace Hopper",
            email="grace@example.com",
            session_id="sess-grace",
        )
        request = self.factory.post(
            "/panel/session/google",
            {"provider": "google", "credential": "google-credential"},
            format="json",
        )
        with (
            patch("identity.views.get_identity_service", return_value=self.service),
            patch("shops.models.Shop.objects") as shop_objects,
        ):
            response = LoginView.as_view()(request)
            shop_objects.filter.assert_not_called()
            shop_objects.get.assert_not_called()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["authenticated"])
        self.assertEqual(response.data["email"], "grace@example.com")

    def test_rf9_relogin_replaces_current_account(self):
        """RF-9: a second successful login leaves the latest account as current."""
        self.service.login_with_google.side_effect = [
            LoginResult(
                authenticated=True,
                name="Account A",
                email="a@example.com",
                session_id="sess-a",
            ),
            LoginResult(
                authenticated=True,
                name="Account B",
                email="b@example.com",
                session_id="sess-b",
            ),
        ]
        first = self.factory.post(
            "/panel/session/google",
            {"provider": "google", "credential": "cred-a"},
            format="json",
        )
        second = self.factory.post(
            "/panel/session/google",
            {"provider": "google", "credential": "cred-b"},
            format="json",
        )
        with patch("identity.views.get_identity_service", return_value=self.service):
            response_a = LoginView.as_view()(first)
            response_b = LoginView.as_view()(second)

        self.assertEqual(response_a.data["email"], "a@example.com")
        self.assertEqual(response_b.data["email"], "b@example.com")
        self.assertEqual(response_b.cookies[SESSION_COOKIE_NAME].value, "sess-b")

        self.service.whoami.return_value = WhoAmIResult(
            authenticated=True,
            name="Account B",
            email="b@example.com",
        )
        whoami_request = self.factory.get("/panel/me")
        whoami_request.COOKIES[SESSION_COOKIE_NAME] = "sess-b"
        with patch("identity.views.get_identity_service", return_value=self.service):
            whoami = WhoAmIView.as_view()(whoami_request)
        self.assertEqual(whoami.data["email"], "b@example.com")
        self.assertEqual(whoami.data["name"], "Account B")

    def test_rf11_google_rejection_does_not_authenticate(self):
        """RF-11: account-api rejection leaves the client unauthenticated with Spanish message."""
        from identity.exceptions import AccountAccessRejected

        self.service.login_with_google.side_effect = AccountAccessRejected("rejected")
        request = self.factory.post(
            "/panel/session/google",
            {"provider": "google", "credential": "bad"},
            format="json",
        )
        with patch("identity.views.get_identity_service", return_value=self.service):
            response = LoginView.as_view()(request)
        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.data["authenticated"])
        self.assertIn("rechazado", response.data["message"].lower())
        self.assertNotIn(SESSION_COOKIE_NAME, response.cookies)

    def test_rf12_account_unavailable_does_not_authenticate(self):
        """RF-12: timeout/5xx leaves unauthenticated with Spanish incomplete-access message."""
        from identity.exceptions import AccountServiceUnavailable

        self.service.login_with_google.side_effect = AccountServiceUnavailable("down")
        request = self.factory.post(
            "/panel/session/google",
            {"provider": "google", "credential": "google-credential"},
            format="json",
        )
        with patch("identity.views.get_identity_service", return_value=self.service):
            response = LoginView.as_view()(request)
        self.assertEqual(response.status_code, 503)
        self.assertFalse(response.data["authenticated"])
        self.assertIn("no pudo completarse", response.data["message"].lower())
        self.assertNotIn(SESSION_COOKIE_NAME, response.cookies)

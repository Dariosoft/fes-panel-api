from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from identity.account_client import SESSION_COOKIE_NAME
from identity.services import LoginResult, WhoAmIResult
from identity.views import LoginView, LogoutView, WhoAmIView


class PostLogoutFlowTests(SimpleTestCase):
    def test_rf6_rf13_login_logout_then_whoami_is_anonymous(self):
        """RF-6, RF-13: after logout, subsequent whoami is anonymous; session closed."""
        factory = APIRequestFactory()
        service = MagicMock()
        service.login_with_google.return_value = LoginResult(
            authenticated=True,
            name="Ada Lovelace",
            email="ada@example.com",
            session_id="sess-1",
        )
        login_request = factory.post(
            "/panel/session/google",
            {"provider": "google", "credential": "google-credential"},
            format="json",
        )
        with patch("identity.views.get_identity_service", return_value=service):
            login_response = LoginView.as_view()(login_request)
        self.assertTrue(login_response.data["authenticated"])

        logout_request = factory.post("/panel/session/logout")
        logout_request.COOKIES[SESSION_COOKIE_NAME] = "sess-1"
        with patch("identity.views.get_identity_service", return_value=service):
            logout_response = LogoutView.as_view()(logout_request)
        self.assertEqual(logout_response.status_code, 200)
        service.logout.assert_called_once_with("sess-1")

        service.whoami.return_value = WhoAmIResult(authenticated=False)
        whoami_request = factory.get("/panel/me")
        with patch("identity.views.get_identity_service", return_value=service):
            whoami = WhoAmIView.as_view()(whoami_request)
        self.assertEqual(whoami.data, {"authenticated": False})
        self.assertNotIn("name", whoami.data)
        self.assertNotIn("email", whoami.data)

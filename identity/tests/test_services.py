from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from identity.account_client import AccountIdentity, SessionResult
from identity.services import IdentityService


class IdentityServiceTests(SimpleTestCase):
    def setUp(self):
        self.client = MagicMock()
        self.service = IdentityService(client=self.client)

    def test_login_with_google_success_without_local_account_writes(self):
        self.client.confirm_google_access.return_value = SessionResult(
            identity=AccountIdentity(name="Ada Lovelace", email="ada@example.com"),
            session_id="sess-1",
        )

        with (
            patch("django.contrib.auth.models.User.objects") as user_objects,
            patch("shops.models.Shop.objects") as shop_objects,
        ):
            result = self.service.login_with_google("google-credential")
            user_objects.create.assert_not_called()
            shop_objects.create.assert_not_called()

        self.assertTrue(result.authenticated)
        self.assertEqual(result.name, "Ada Lovelace")
        self.assertEqual(result.email, "ada@example.com")
        self.assertEqual(result.session_id, "sess-1")
        self.client.confirm_google_access.assert_called_once_with("google-credential")

    def test_logout_closes_shared_session(self):
        self.service.logout("sess-1")
        self.client.close_session.assert_called_once_with("sess-1")

    def test_whoami_authenticated(self):
        self.client.get_identity.return_value = AccountIdentity(
            name="Ada Lovelace",
            email="ada@example.com",
        )
        result = self.service.whoami("sess-1")
        self.assertTrue(result.authenticated)
        self.assertEqual(result.name, "Ada Lovelace")
        self.assertEqual(result.email, "ada@example.com")

    def test_whoami_anonymous(self):
        self.client.get_identity.return_value = None
        result = self.service.whoami(None)
        self.assertFalse(result.authenticated)
        self.assertIsNone(result.name)
        self.assertIsNone(result.email)

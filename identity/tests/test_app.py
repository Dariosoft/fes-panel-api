from django.apps import apps
from django.conf import settings
from django.test import SimpleTestCase, override_settings


class IdentityAppTests(SimpleTestCase):
    def test_identity_app_is_installed(self):
        self.assertIn("identity", settings.INSTALLED_APPS)
        self.assertTrue(apps.is_installed("identity"))


class AccountApiSettingsTests(SimpleTestCase):
    def test_settings_expose_account_api_url_and_timeout(self):
        self.assertTrue(hasattr(settings, "ACCOUNT_API_BASE_URL"))
        self.assertTrue(hasattr(settings, "ACCOUNT_API_TIMEOUT_SECONDS"))
        self.assertIsInstance(settings.ACCOUNT_API_BASE_URL, str)
        self.assertIsInstance(settings.ACCOUNT_API_TIMEOUT_SECONDS, float)

    @override_settings(
        ACCOUNT_API_BASE_URL="http://accounts.test:9000",
        ACCOUNT_API_TIMEOUT_SECONDS=2.5,
    )
    def test_settings_can_be_overridden_from_environment_values(self):
        self.assertEqual(settings.ACCOUNT_API_BASE_URL, "http://accounts.test:9000")
        self.assertEqual(settings.ACCOUNT_API_TIMEOUT_SECONDS, 2.5)

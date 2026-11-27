from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from common.infrastructure import (
    build_account_api_gateway,
    build_analytics_api_gateway,
    build_catalog_api_gateway,
    build_notifications_api_gateway,
)


@override_settings(
    ACCOUNT_API_BASE_URL="http://account-api.test:8080",
    ACCOUNT_API_TIMEOUT_SECONDS=2.5,
    CATALOG_API_BASE_URL="http://catalog-api.test:8080",
    CATALOG_API_TIMEOUT_SECONDS=3.5,
    ANALYTICS_API_BASE_URL="http://analytics-api.test:8080",
    ANALYTICS_API_TIMEOUT_SECONDS=4.5,
    NOTIFICATIONS_API_BASE_URL="http://notifications-api.test:8080",
)
class ClientFactoryTests(SimpleTestCase):
    def test_builds_account_gateway_from_settings(self):
        with patch("common.infrastructure.client_factory.AccountApiClient") as client_type:
            gateway = build_account_api_gateway()

        client_type.assert_called_once_with(
            base_url="http://account-api.test:8080",
            timeout_seconds=2.5,
        )
        self.assertIs(gateway, client_type.return_value)

    def test_builds_catalog_gateway_from_settings(self):
        with patch("common.infrastructure.client_factory.CatalogApiClient") as client_type:
            gateway = build_catalog_api_gateway()

        client_type.assert_called_once_with(
            base_url="http://catalog-api.test:8080",
            timeout_seconds=3.5,
        )
        self.assertIs(gateway, client_type.return_value)

    def test_builds_analytics_gateway_from_settings(self):
        with patch("common.infrastructure.client_factory.AnalyticsApiClient") as client_type:
            gateway = build_analytics_api_gateway()

        client_type.assert_called_once_with(
            base_url="http://analytics-api.test:8080",
            timeout_seconds=4.5,
        )
        self.assertIs(gateway, client_type.return_value)

    def test_builds_notifications_gateway_from_settings(self):
        with patch("common.infrastructure.client_factory.NotificationsApiClient") as client_type:
            gateway = build_notifications_api_gateway()

        client_type.assert_called_once_with(base_url="http://notifications-api.test:8080")
        self.assertIs(gateway, client_type.return_value)

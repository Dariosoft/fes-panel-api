from django.conf import settings

from common.infrastructure.clients import (
    AccountApiClient,
    AnalyticsApiClient,
    CatalogApiClient,
    NotificationsApiClient,
)
from common.ports import (
    AccountApiGateway,
    AnalyticsApiGateway,
    CatalogApiGateway,
    NotificationsApiGateway,
)


def build_account_api_gateway() -> AccountApiGateway:
    return AccountApiClient(
        base_url=settings.ACCOUNT_API_BASE_URL,
        timeout_seconds=settings.ACCOUNT_API_TIMEOUT_SECONDS,
    )


def build_catalog_api_gateway() -> CatalogApiGateway:
    return CatalogApiClient(
        base_url=settings.CATALOG_API_BASE_URL,
        timeout_seconds=settings.CATALOG_API_TIMEOUT_SECONDS,
    )


def build_analytics_api_gateway() -> AnalyticsApiGateway:
    return AnalyticsApiClient(
        base_url=settings.ANALYTICS_API_BASE_URL,
        timeout_seconds=settings.ANALYTICS_API_TIMEOUT_SECONDS,
    )


def build_notifications_api_gateway() -> NotificationsApiGateway:
    return NotificationsApiClient(base_url=settings.NOTIFICATIONS_API_BASE_URL)

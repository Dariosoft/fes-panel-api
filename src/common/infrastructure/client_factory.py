from django.conf import settings

from common.infrastructure.clients import AccountApiClient, CatalogApiClient
from common.ports import AccountApiGateway, CatalogApiGateway


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

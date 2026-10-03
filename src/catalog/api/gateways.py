from django.conf import settings

from catalog.infrastructure.account_session_client import AccountSessionClient
from catalog.infrastructure.catalog_api_client import CatalogApiClient


def build_session_gateway() -> AccountSessionClient:
    return AccountSessionClient(
        base_url=settings.ACCOUNT_API_BASE_URL,
        timeout_seconds=settings.ACCOUNT_API_TIMEOUT_SECONDS,
    )


def build_catalog_gateway() -> CatalogApiClient:
    return CatalogApiClient(
        base_url=settings.CATALOG_API_BASE_URL,
        timeout_seconds=settings.CATALOG_API_TIMEOUT_SECONDS,
    )

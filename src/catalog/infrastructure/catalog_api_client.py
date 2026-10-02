from urllib.parse import urlencode

from catalog.domain.errors import CatalogServiceUnavailable
from catalog.dtos import CatalogResponse
from common.contracts.catalog_api import (
    CATALOG_PRODUCT_ITEM_PATH,
    CATALOG_PRODUCT_PUBLISH_PATH,
    CATALOG_PRODUCT_UNPUBLISH_PATH,
    CATALOG_PRODUCTS_PATH,
    CATALOG_PUBLISH_PATH,
    OWNER_ACCOUNT_ID_QUERY_PARAM,
)
from common.http import JsonRequest, RemoteServiceError, request_json


class CatalogApiClient:
    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def list_products(self, owner_account_id: str) -> CatalogResponse:
        return self._send("GET", CATALOG_PRODUCTS_PATH, owner_account_id)

    def create_product(
        self,
        owner_account_id: str,
        body: bytes,
        content_type: str | None,
    ) -> CatalogResponse:
        return self._send("POST", CATALOG_PRODUCTS_PATH, owner_account_id, body, content_type)

    def update_product(
        self,
        owner_account_id: str,
        product_id: str,
        body: bytes,
        content_type: str | None,
    ) -> CatalogResponse:
        path = CATALOG_PRODUCT_ITEM_PATH.format(product_id=product_id)
        return self._send("PUT", path, owner_account_id, body, content_type)

    def delete_product(self, owner_account_id: str, product_id: str) -> CatalogResponse:
        path = CATALOG_PRODUCT_ITEM_PATH.format(product_id=product_id)
        return self._send("DELETE", path, owner_account_id)

    def publish_product(self, owner_account_id: str, product_id: str) -> CatalogResponse:
        path = CATALOG_PRODUCT_PUBLISH_PATH.format(product_id=product_id)
        return self._send("POST", path, owner_account_id)

    def unpublish_product(self, owner_account_id: str, product_id: str) -> CatalogResponse:
        path = CATALOG_PRODUCT_UNPUBLISH_PATH.format(product_id=product_id)
        return self._send("POST", path, owner_account_id)

    def publish_catalog(
        self,
        owner_account_id: str,
        body: bytes,
        content_type: str | None,
    ) -> CatalogResponse:
        return self._send("POST", CATALOG_PUBLISH_PATH, owner_account_id, body, content_type)

    def _send(
        self,
        method: str,
        path: str,
        owner_account_id: str,
        body: bytes | None = None,
        content_type: str | None = None,
    ) -> CatalogResponse:
        call = JsonRequest(
            method=method,
            path=self._with_owner(path, owner_account_id),
            timeout_seconds=self._timeout_seconds,
            body=body,
            content_type=content_type,
        )
        try:
            status_code, response_body = request_json(self._base_url, call)
        except RemoteServiceError as exc:
            raise CatalogServiceUnavailable from exc
        return CatalogResponse(status_code=status_code, body=response_body)

    @staticmethod
    def _with_owner(path: str, owner_account_id: str) -> str:
        query = urlencode({OWNER_ACCOUNT_ID_QUERY_PARAM: owner_account_id})
        return f"{path}?{query}"

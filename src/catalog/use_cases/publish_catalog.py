from catalog.dtos import CatalogResponse
from catalog.ports import CatalogGateway


def publish_catalog(
    catalog_gateway: CatalogGateway,
    owner_account_id: str,
    body: bytes,
    content_type: str | None,
) -> CatalogResponse:
    return catalog_gateway.publish_catalog(owner_account_id, body, content_type)

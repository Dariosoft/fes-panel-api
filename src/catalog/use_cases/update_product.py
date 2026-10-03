from catalog.dtos import CatalogResponse
from catalog.ports import CatalogGateway


def update_product(
    catalog_gateway: CatalogGateway,
    owner_account_id: str,
    product_id: str,
    body: bytes,
    content_type: str | None,
) -> CatalogResponse:
    return catalog_gateway.update_product(owner_account_id, product_id, body, content_type)

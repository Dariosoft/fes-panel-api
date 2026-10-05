from common.dtos import ServiceResponse
from common.ports import CatalogApiGateway


def update_product(
    catalog_gateway: CatalogApiGateway,
    owner_account_id: str,
    product_id: str,
    body: bytes,
    content_type: str | None,
) -> ServiceResponse:
    return catalog_gateway.update_product(owner_account_id, product_id, body, content_type)

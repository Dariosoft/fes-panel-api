from common.dtos import ServiceResponse
from common.ports import CatalogApiGateway


def create_product(
    catalog_gateway: CatalogApiGateway,
    owner_account_id: str,
    body: bytes,
    content_type: str | None,
) -> ServiceResponse:
    return catalog_gateway.create_product(owner_account_id, body, content_type)

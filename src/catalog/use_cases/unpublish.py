from common.dtos import ServiceResponse
from common.ports import CatalogApiGateway


def unpublish(
    catalog_gateway: CatalogApiGateway,
    owner_account_id: str,
    product_id: str,
) -> ServiceResponse:
    return catalog_gateway.unpublish(owner_account_id, product_id)

from common.dtos import ServiceResponse
from common.ports import CatalogApiGateway


def delete_product(
    catalog_gateway: CatalogApiGateway,
    owner_account_id: str,
    product_id: str,
) -> ServiceResponse:
    return catalog_gateway.delete_product(owner_account_id, product_id)

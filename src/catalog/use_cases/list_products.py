from common.dtos import ServiceResponse
from common.ports import CatalogApiGateway


def list_products(
    catalog_gateway: CatalogApiGateway,
    owner_account_id: str,
    name: str | None = None,
) -> ServiceResponse:
    return catalog_gateway.list_products(owner_account_id, name)

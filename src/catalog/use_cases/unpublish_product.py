from catalog.dtos import CatalogResponse
from catalog.ports import CatalogGateway


def unpublish_product(
    catalog_gateway: CatalogGateway,
    owner_account_id: str,
    product_id: str,
) -> CatalogResponse:
    return catalog_gateway.unpublish_product(owner_account_id, product_id)

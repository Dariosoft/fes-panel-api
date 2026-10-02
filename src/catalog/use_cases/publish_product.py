from catalog.dtos import CatalogResponse
from catalog.ports import CatalogGateway


def publish_product(
    catalog_gateway: CatalogGateway,
    owner_account_id: str,
    product_id: str,
) -> CatalogResponse:
    return catalog_gateway.publish_product(owner_account_id, product_id)

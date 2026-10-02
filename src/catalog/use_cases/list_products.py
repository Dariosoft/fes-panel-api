from catalog.dtos import CatalogResponse
from catalog.ports import CatalogGateway


def list_products(catalog_gateway: CatalogGateway, owner_account_id: str) -> CatalogResponse:
    return catalog_gateway.list_products(owner_account_id)

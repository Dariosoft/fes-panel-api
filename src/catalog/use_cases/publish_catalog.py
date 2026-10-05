from common.dtos import ServiceResponse
from common.ports import CatalogApiGateway


def publish_catalog(
    catalog_gateway: CatalogApiGateway,
    owner_account_id: str,
    body: bytes,
    content_type: str | None,
) -> ServiceResponse:
    return catalog_gateway.publish_catalog(owner_account_id, body, content_type)

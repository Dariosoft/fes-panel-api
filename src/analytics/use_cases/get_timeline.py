from common.dtos import ServiceResponse
from common.ports import AnalyticsApiGateway


def get_timeline(
    gateway: AnalyticsApiGateway,
    tenant_id: str,
    order_id: str | None = None,
) -> ServiceResponse:
    return gateway.timeline(tenant_id, order_id)

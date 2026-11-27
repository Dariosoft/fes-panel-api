from common.dtos import ServiceResponse
from common.ports import AnalyticsApiGateway


def get_metrics(gateway: AnalyticsApiGateway, tenant_id: str) -> ServiceResponse:
    return gateway.metrics(tenant_id)

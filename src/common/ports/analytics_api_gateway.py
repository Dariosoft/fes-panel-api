from typing import Protocol

from common.dtos import ServiceResponse


class AnalyticsApiGateway(Protocol):
    def timeline(self, tenant_id: str, order_id: str | None = None) -> ServiceResponse:
        """Fetch the tenant order timeline from the analytics API."""

    def metrics(self, tenant_id: str) -> ServiceResponse:
        """Fetch the tenant metrics from the analytics API."""

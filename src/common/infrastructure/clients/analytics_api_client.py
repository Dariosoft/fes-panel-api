from urllib.parse import urlencode

from common.contracts.analytics_api import (
    ANALYTICS_METRICS_PATH,
    ANALYTICS_TIMELINE_PATH,
    ORDER_ID_QUERY_PARAM,
    TENANT_ID_QUERY_PARAM,
)
from common.dtos import ServiceResponse
from common.errors import AnalyticsApiTimeout, AnalyticsApiUnavailable
from common.http import JsonRequest, RemoteServiceError, is_timeout_error, request_json


class AnalyticsApiClient:
    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def timeline(self, tenant_id: str, order_id: str | None = None) -> ServiceResponse:
        params = {TENANT_ID_QUERY_PARAM: tenant_id}
        if order_id:
            params[ORDER_ID_QUERY_PARAM] = order_id
        return self._get(ANALYTICS_TIMELINE_PATH, params)

    def metrics(self, tenant_id: str) -> ServiceResponse:
        return self._get(ANALYTICS_METRICS_PATH, {TENANT_ID_QUERY_PARAM: tenant_id})

    def _get(self, path: str, params: dict[str, str]) -> ServiceResponse:
        call = JsonRequest(
            method="GET",
            path=f"{path}?{urlencode(params)}",
            timeout_seconds=self._timeout_seconds,
        )
        try:
            status_code, response_body = request_json(self._base_url, call)
        except RemoteServiceError as exc:
            if is_timeout_error(exc):
                raise AnalyticsApiTimeout from exc
            raise AnalyticsApiUnavailable from exc
        return ServiceResponse(status_code=status_code, body=response_body)

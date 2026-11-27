from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from analytics.api.panel_session import PanelAnalyticsSessionGuardMixin
from analytics.use_cases import get_metrics, get_timeline


class PanelAnalyticsTimelineView(PanelAnalyticsSessionGuardMixin, APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request: Request) -> Response:
        order_id = request.query_params.get("orderId")
        return self._forward(lambda gateway: get_timeline(gateway, self.tenant_id, order_id))


class PanelAnalyticsMetricsView(PanelAnalyticsSessionGuardMixin, APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request: Request) -> Response:
        return self._forward(lambda gateway: get_metrics(gateway, self.tenant_id))

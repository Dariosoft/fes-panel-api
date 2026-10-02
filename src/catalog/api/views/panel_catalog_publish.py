from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.api.panel_session import PanelSessionGuardMixin
from catalog.use_cases import publish_catalog


class PanelCatalogPublishView(PanelSessionGuardMixin, APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request: Request) -> Response:
        return self._forward(
            lambda gateway: publish_catalog(
                gateway,
                self.owner_account_id,
                request.body,
                request.content_type,
            )
        )

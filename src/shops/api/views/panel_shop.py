from collections.abc import Callable

from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.contracts.account_api import SESSION_COOKIE_NAME
from common.dtos import ServiceResponse
from common.errors import AccountApiUnavailable
from common.infrastructure import build_account_api_gateway
from common.ports import AccountApiGateway
from shops.use_cases import get_shop, save_shop

_UNAVAILABLE_BODY = {
    "error": "servicio_no_disponible",
    "message": "El servicio de cuentas no está disponible. Inténtalo de nuevo más tarde.",
}


class PanelShopView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request: Request) -> Response:
        return self._forward(lambda gateway: get_shop(gateway, self._fes_session(request)))

    def put(self, request: Request) -> Response:
        content_type = request.META.get("CONTENT_TYPE") or "application/json"
        return self._forward(
            lambda gateway: save_shop(
                gateway,
                self._fes_session(request),
                request.body,
                content_type,
            )
        )

    def _fes_session(self, request: Request) -> str | None:
        return request.COOKIES.get(SESSION_COOKIE_NAME)

    def _forward(
        self,
        operation: Callable[[AccountApiGateway], ServiceResponse],
    ) -> Response:
        try:
            result = operation(build_account_api_gateway())
        except AccountApiUnavailable:
            return Response(_UNAVAILABLE_BODY, status=503)
        return Response(result.body, status=result.status_code)

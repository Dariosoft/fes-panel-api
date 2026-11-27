from collections.abc import Callable

from rest_framework.exceptions import APIException
from rest_framework.request import Request
from rest_framework.response import Response

from analytics.use_cases import resolve_panel_tenant
from common.contracts.account_api import SESSION_COOKIE_NAME
from common.dtos import ServiceResponse
from common.errors import AccountApiUnavailable, AnalyticsApiTimeout, AnalyticsApiUnavailable
from common.infrastructure import build_account_api_gateway, build_analytics_api_gateway
from common.ports import AccountApiGateway, AnalyticsApiGateway

_SESSION_UNAVAILABLE_BODY = {
    "error": "servicio_no_disponible",
    "message": "El servicio de cuentas no está disponible. Inténtalo de nuevo más tarde.",
}
_UNAUTHENTICATED_BODY = {
    "error": "no_autenticado",
    "message": "Debes iniciar sesión para consultar la analítica.",
}
_ANALYTICS_UNAVAILABLE_BODY = {
    "error": "servicio_no_disponible",
    "message": "El servicio de analítica no está disponible. Inténtalo de nuevo más tarde.",
}
_ANALYTICS_TIMEOUT_BODY = {
    "error": "tiempo_de_espera_agotado",
    "message": "El servicio de analítica tardó demasiado en responder. "
    "Inténtalo de nuevo más tarde.",
}


class _SessionUnavailable(APIException):
    status_code = 503
    default_code = "servicio_no_disponible"


class _Unauthenticated(APIException):
    status_code = 401
    default_code = "no_autenticado"


class PanelAnalyticsSessionGuardMixin:
    tenant_id: str

    def _session_gateway(self) -> AccountApiGateway:
        return build_account_api_gateway()

    def _analytics_gateway(self) -> AnalyticsApiGateway:
        return build_analytics_api_gateway()

    def initial(self, request: Request, *args, **kwargs) -> None:
        super().initial(request, *args, **kwargs)
        fes_session = request.COOKIES.get(SESSION_COOKIE_NAME)
        try:
            tenant_id = resolve_panel_tenant(self._session_gateway(), fes_session)
        except AccountApiUnavailable:
            raise _SessionUnavailable from None
        if tenant_id is None:
            raise _Unauthenticated
        self.tenant_id = tenant_id

    def handle_exception(self, exc: Exception) -> Response:
        if isinstance(exc, _SessionUnavailable):
            return Response(_SESSION_UNAVAILABLE_BODY, status=503)
        if isinstance(exc, _Unauthenticated):
            return Response(_UNAUTHENTICATED_BODY, status=401)
        return super().handle_exception(exc)

    def _forward(
        self,
        operation: Callable[[AnalyticsApiGateway], ServiceResponse],
    ) -> Response:
        try:
            result = operation(self._analytics_gateway())
        except AnalyticsApiTimeout:
            return Response(_ANALYTICS_TIMEOUT_BODY, status=504)
        except AnalyticsApiUnavailable:
            return Response(_ANALYTICS_UNAVAILABLE_BODY, status=502)
        return Response(result.body, status=result.status_code)

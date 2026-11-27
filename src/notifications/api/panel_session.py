from rest_framework.exceptions import APIException
from rest_framework.request import Request
from rest_framework.response import Response

from common.contracts.account_api import SESSION_COOKIE_NAME
from common.errors import AccountApiUnavailable
from common.infrastructure import build_account_api_gateway, build_notifications_api_gateway
from common.ports import AccountApiGateway, NotificationsApiGateway
from notifications.use_cases import resolve_panel_tenant

_SESSION_UNAVAILABLE_BODY = {
    "error": "servicio_no_disponible",
    "message": "El servicio de cuentas no está disponible. Inténtalo de nuevo más tarde.",
}
_UNAUTHENTICATED_BODY = {
    "error": "no_autenticado",
    "message": "Debes iniciar sesión para consultar las notificaciones.",
}


class _SessionUnavailable(APIException):
    status_code = 503
    default_code = "servicio_no_disponible"


class _Unauthenticated(APIException):
    status_code = 401
    default_code = "no_autenticado"


class PanelNotificationsSessionGuardMixin:
    tenant_id: str

    def _session_gateway(self) -> AccountApiGateway:
        return build_account_api_gateway()

    def _notifications_gateway(self) -> NotificationsApiGateway:
        return build_notifications_api_gateway()

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

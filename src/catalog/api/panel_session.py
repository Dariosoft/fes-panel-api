from collections.abc import Callable

from rest_framework.exceptions import APIException
from rest_framework.request import Request
from rest_framework.response import Response

from catalog.api.gateways import build_catalog_gateway, build_session_gateway
from catalog.domain.constants import SESSION_COOKIE_NAME
from catalog.domain.errors import CatalogServiceUnavailable, SessionServiceUnavailable
from catalog.dtos import CatalogResponse
from catalog.infrastructure.account_session_client import AccountSessionClient
from catalog.infrastructure.catalog_api_client import CatalogApiClient
from catalog.ports import CatalogGateway
from catalog.use_cases import resolve_panel_owner

_SESSION_UNAVAILABLE_BODY = {
    "error": "servicio_no_disponible",
    "message": "El servicio de cuentas no está disponible. Inténtalo de nuevo más tarde.",
}
_UNAUTHENTICATED_BODY = {
    "error": "no_autenticado",
    "message": "Debes iniciar sesión para operar el catálogo.",
}
_CATALOG_UNAVAILABLE_BODY = {
    "error": "servicio_no_disponible",
    "message": "El servicio de catálogo no está disponible. Inténtalo de nuevo más tarde.",
}


class _SessionUnavailable(APIException):
    status_code = 503
    default_code = "servicio_no_disponible"


class _Unauthenticated(APIException):
    status_code = 401
    default_code = "no_autenticado"


class PanelSessionGuardMixin:
    owner_account_id: str

    def _session_gateway(self) -> AccountSessionClient:
        return build_session_gateway()

    def _catalog_gateway(self) -> CatalogApiClient:
        return build_catalog_gateway()

    def initial(self, request: Request, *args, **kwargs) -> None:
        super().initial(request, *args, **kwargs)
        fes_session = request.COOKIES.get(SESSION_COOKIE_NAME)
        try:
            session = resolve_panel_owner(self._session_gateway(), fes_session)
        except SessionServiceUnavailable:
            raise _SessionUnavailable from None
        if not session.authenticated or not session.account_id:
            raise _Unauthenticated
        self.owner_account_id = session.account_id

    def handle_exception(self, exc: Exception) -> Response:
        if isinstance(exc, _SessionUnavailable):
            return Response(_SESSION_UNAVAILABLE_BODY, status=503)
        if isinstance(exc, _Unauthenticated):
            return Response(_UNAUTHENTICATED_BODY, status=401)
        return super().handle_exception(exc)

    def _forward(
        self,
        operation: Callable[[CatalogGateway], CatalogResponse],
    ) -> Response:
        try:
            result = operation(self._catalog_gateway())
            print(f"Operation result: {result}")
        except CatalogServiceUnavailable:
            print("Catalog service unavailable")
            return Response(_CATALOG_UNAVAILABLE_BODY, status=503)
        print(f"Sigue de largo")
        return Response(result.body, status=result.status_code)

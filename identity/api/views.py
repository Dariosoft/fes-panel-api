from django.conf import settings
from django.http import HttpResponseRedirect
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from identity.api.cookies import clear_session_cookie
from identity.application.build_google_login_redirect import build_google_login_redirect
from identity.application.logout_panel_session import logout_panel_session
from identity.application.resolve_panel_session import resolve_panel_session
from identity.domain.constants import SESSION_COOKIE_NAME
from identity.domain.errors import AccountServiceUnavailable
from identity.infrastructure.account_session_client import AccountSessionClient

_UNAVAILABLE_BODY = {
    "error": "servicio_no_disponible",
    "message": "El servicio de cuentas no está disponible. Inténtalo de nuevo más tarde.",
}


def _gateway() -> AccountSessionClient:
    return AccountSessionClient(
        base_url=settings.ACCOUNT_API_BASE_URL,
        timeout_seconds=settings.ACCOUNT_API_TIMEOUT_SECONDS,
    )


class GoogleLoginRedirectView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, _request: Request) -> HttpResponseRedirect:
        location = build_google_login_redirect(
            settings.ACCOUNTS_PUBLIC_BASE_URL,
            settings.PANEL_PUBLIC_ORIGIN,
        )
        return HttpResponseRedirect(location)


class PanelSessionView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request: Request) -> Response:
        fes_session = request.COOKIES.get(SESSION_COOKIE_NAME)
        try:
            payload = resolve_panel_session(_gateway(), fes_session)
        except AccountServiceUnavailable:
            return Response(_UNAVAILABLE_BODY, status=503)
        return Response(payload.body, status=payload.status_code)


class PanelLogoutView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request: Request) -> Response:
        fes_session = request.COOKIES.get(SESSION_COOKIE_NAME)
        try:
            result = logout_panel_session(_gateway(), fes_session)
        except AccountServiceUnavailable:
            return Response(_UNAVAILABLE_BODY, status=503)
        response = Response(result.body, status=result.status_code)
        if result.clear_cookie:
            clear_session_cookie(response)
        return response

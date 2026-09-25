"""DRF views for panel identity door (login / logout / whoami)."""

from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from identity.account_client import SESSION_COOKIE_NAME
from identity.exceptions import AccountAccessRejected, AccountServiceUnavailable
from identity.services import IdentityService, WhoAmIResult

SUPPORTED_LOGIN_PROVIDER = "google"


def get_identity_service() -> IdentityService:
    return IdentityService()


def _session_id_from_request(request: Request) -> str | None:
    return request.COOKIES.get(SESSION_COOKIE_NAME)


def _whoami_payload(result: WhoAmIResult) -> dict:
    if not result.authenticated:
        return {"authenticated": False}
    return {
        "authenticated": True,
        "name": result.name,
        "email": result.email,
    }


def _set_session_cookie(response: Response, session_id: str) -> None:
    response.set_cookie(
        SESSION_COOKIE_NAME,
        session_id,
        httponly=True,
        samesite="Lax",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE_NAME)


class WhoAmIView(APIView):
    """RF-1, RF-8, RF-13 — report current shared-session identity."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def get(self, request: Request) -> Response:
        result = get_identity_service().whoami(_session_id_from_request(request))
        return Response(_whoami_payload(result), status=status.HTTP_200_OK)


class LogoutView(APIView):
    """RF-6, RF-10, RF-13 — close shared session (idempotent)."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request: Request) -> Response:
        get_identity_service().logout(_session_id_from_request(request))
        response = Response({"authenticated": False}, status=status.HTTP_200_OK)
        _clear_session_cookie(response)
        return response


class LoginView(APIView):
    """RF-2…RF-5, RF-9, RF-11, RF-12 — enter with Google only."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request: Request) -> Response:
        provider = (request.data.get("provider") or SUPPORTED_LOGIN_PROVIDER).strip().lower()
        if provider != SUPPORTED_LOGIN_PROVIDER:
            return Response(
                {
                    "authenticated": False,
                    "message": "Solo se admite el acceso con Google en esta iteración.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        credential = request.data.get("credential")
        if not credential or not isinstance(credential, str):
            return Response(
                {
                    "authenticated": False,
                    "message": "Se requiere la credencial de Google.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = get_identity_service().login_with_google(credential)
        except AccountAccessRejected:
            return Response(
                {
                    "authenticated": False,
                    "message": "El acceso con Google fue rechazado.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except AccountServiceUnavailable:
            return Response(
                {
                    "authenticated": False,
                    "message": "El acceso no pudo completarse. Inténtalo de nuevo más tarde.",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        response = Response(
            {
                "authenticated": True,
                "name": result.name,
                "email": result.email,
            },
            status=status.HTTP_200_OK,
        )
        _set_session_cookie(response, result.session_id)
        return response

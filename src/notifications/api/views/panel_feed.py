from collections.abc import Iterator
from typing import IO

from django.http import StreamingHttpResponse
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.errors import NotificationsApiTimeout, NotificationsApiUnavailable
from notifications.api.panel_session import PanelNotificationsSessionGuardMixin
from notifications.use_cases import open_feed

_STREAM_CHUNK_SIZE = 4096
_NOTIFICATIONS_UNAVAILABLE_BODY = {
    "error": "servicio_no_disponible",
    "message": "El servicio de notificaciones no está disponible. Inténtalo de nuevo más tarde.",
}
_NOTIFICATIONS_TIMEOUT_BODY = {
    "error": "tiempo_de_espera_agotado",
    "message": "El servicio de notificaciones tardó demasiado en responder.",
}


class PanelFeedView(PanelNotificationsSessionGuardMixin, APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request: Request) -> StreamingHttpResponse | Response:
        try:
            upstream = open_feed(self._notifications_gateway(), self.tenant_id)
        except NotificationsApiTimeout:
            return Response(_NOTIFICATIONS_TIMEOUT_BODY, status=504)
        except NotificationsApiUnavailable:
            return Response(_NOTIFICATIONS_UNAVAILABLE_BODY, status=502)
        response = StreamingHttpResponse(
            self._stream(upstream),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response

    @staticmethod
    def _stream(upstream: IO[bytes]) -> Iterator[bytes]:
        try:
            while chunk := upstream.read(_STREAM_CHUNK_SIZE):
                yield chunk
        finally:
            upstream.close()

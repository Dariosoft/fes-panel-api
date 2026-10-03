from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.api.panel_session import PanelSessionGuardMixin
from catalog.domain import SESSION_COOKIE_NAME, SessionServiceUnavailable
from catalog.dtos import PanelSession


class _ProbeView(PanelSessionGuardMixin, APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request) -> Response:
        return Response({"owner_account_id": self.owner_account_id})


class _SessionGateway:
    def __init__(self, session: PanelSession | None = None, error: Exception | None = None):
        self._session = session
        self._error = error
        self.last_cookie = None

    def resolve(self, fes_session: str | None) -> PanelSession:
        self.last_cookie = fes_session
        if self._error:
            raise self._error
        return self._session


class PanelSessionGuardTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = _ProbeView.as_view()

    def _call(self, gateway, cookie: str | None = None):
        headers = {"HTTP_COOKIE": f"{SESSION_COOKIE_NAME}={cookie}"} if cookie else {}
        with patch.object(_ProbeView, "_session_gateway", return_value=gateway):
            return self.view(self.factory.get("/probe", **headers))

    def test_missing_cookie_is_unauthorized(self):
        gateway = _SessionGateway(PanelSession(authenticated=False, account_id=None))

        response = self._call(gateway)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["error"], "no_autenticado")
        self.assertIn("message", response.data)

    def test_anonymous_session_is_unauthorized(self):
        gateway = _SessionGateway(PanelSession(authenticated=False, account_id=None))

        response = self._call(gateway, cookie="tok")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["error"], "no_autenticado")
        self.assertEqual(gateway.last_cookie, "tok")

    def test_accounts_failure_is_unavailable(self):
        gateway = _SessionGateway(error=SessionServiceUnavailable())

        response = self._call(gateway, cookie="tok")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data["error"], "servicio_no_disponible")

    def test_valid_session_continues_and_keeps_owner(self):
        gateway = _SessionGateway(PanelSession(authenticated=True, account_id="acc-1"))

        response = self._call(gateway, cookie="tok")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["owner_account_id"], "acc-1")
        self.assertEqual(gateway.last_cookie, "tok")

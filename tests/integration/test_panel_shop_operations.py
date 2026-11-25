import json
from pathlib import Path
from unittest.mock import patch

from django.apps import apps
from django.test import SimpleTestCase
from rest_framework.test import APIClient

from common.contracts.account_api import SESSION_COOKIE_NAME
from common.dtos import ServiceResponse
from common.errors import AccountApiUnavailable


class _ShopGateway:
    def __init__(self, response=None, error=None):
        self._response = response or ServiceResponse(status_code=200, body={"ok": True})
        self._error = error
        self.calls: list[tuple] = []

    def get_shop(self, fes_session):
        self.calls.append(("get_shop", fes_session))
        if self._error:
            raise self._error
        return self._response

    def save_shop(self, fes_session, body, content_type):
        self.calls.append(("save_shop", fes_session, body, content_type))
        if self._error:
            raise self._error
        return self._response


class PanelShopOperationTests(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()

    def _run(self, method, path, gateway, **kwargs):
        with patch(
            "shops.api.views.panel_shop.build_account_api_gateway",
            lambda: gateway,
        ):
            return getattr(self.client, method)(path, **kwargs)

    def test_get_shop_retransmits_body_and_forwards_cookie(self):
        self.client.cookies[SESSION_COOKIE_NAME] = "tok"
        body = {"name": "Mi tienda", "description": None}
        gateway = _ShopGateway(response=ServiceResponse(status_code=200, body=body))

        response = self._run("get", "/panel/shop", gateway)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), body)
        self.assertEqual(gateway.calls, [("get_shop", "tok")])

    def test_get_shop_propagates_not_found(self):
        self.client.cookies[SESSION_COOKIE_NAME] = "tok"
        gateway = _ShopGateway(
            response=ServiceResponse(status_code=404, body={"error": "sin_tienda"})
        )

        response = self._run("get", "/panel/shop", gateway)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"error": "sin_tienda"})

    def test_get_shop_without_session_propagates_unauthorized(self):
        gateway = _ShopGateway(
            response=ServiceResponse(status_code=401, body={"error": "no_autenticado"})
        )

        response = self._run("get", "/panel/shop", gateway)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(gateway.calls, [("get_shop", None)])

    def test_put_shop_forwards_body_and_content_type(self):
        self.client.cookies[SESSION_COOKIE_NAME] = "tok"
        payload = {"name": "Mi tienda", "description": "Hola"}
        body = json.dumps(payload).encode("utf-8")
        gateway = _ShopGateway(response=ServiceResponse(status_code=200, body=payload))

        response = self._run(
            "put",
            "/panel/shop",
            gateway,
            data=body,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), payload)
        method, session, forwarded_body, content_type = gateway.calls[0]
        self.assertEqual((method, session), ("save_shop", "tok"))
        self.assertEqual(forwarded_body, body)
        self.assertEqual(content_type, "application/json")

    def test_put_shop_propagates_validation_rejection(self):
        self.client.cookies[SESSION_COOKIE_NAME] = "tok"
        body = {"error": "datos_invalidos", "message": "El nombre es obligatorio."}
        gateway = _ShopGateway(response=ServiceResponse(status_code=422, body=body))

        response = self._run(
            "put",
            "/panel/shop",
            gateway,
            data={"name": ""},
            format="json",
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json(), body)

    def test_put_shop_without_session_propagates_unauthorized(self):
        gateway = _ShopGateway(
            response=ServiceResponse(status_code=401, body={"error": "no_autenticado"})
        )

        response = self._run(
            "put",
            "/panel/shop",
            gateway,
            data={"name": "Mi tienda"},
            format="json",
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(gateway.calls[0][1], None)

    def test_get_shop_unavailable_returns_503_and_keeps_cookie(self):
        self.client.cookies[SESSION_COOKIE_NAME] = "tok"
        gateway = _ShopGateway(error=AccountApiUnavailable())

        response = self._run("get", "/panel/shop", gateway)

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {
                "error": "servicio_no_disponible",
                "message": "El servicio de cuentas no está disponible. "
                "Inténtalo de nuevo más tarde.",
            },
        )
        self.assertNotIn(SESSION_COOKIE_NAME, response.cookies)
        self.assertEqual(self.client.cookies[SESSION_COOKIE_NAME].value, "tok")

    def test_put_shop_unavailable_returns_503_and_keeps_cookie(self):
        self.client.cookies[SESSION_COOKIE_NAME] = "tok"
        gateway = _ShopGateway(error=AccountApiUnavailable())

        response = self._run(
            "put",
            "/panel/shop",
            gateway,
            data={"name": "Mi tienda"},
            format="json",
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"], "servicio_no_disponible")
        self.assertNotIn(SESSION_COOKIE_NAME, response.cookies)
        self.assertEqual(self.client.cookies[SESSION_COOKIE_NAME].value, "tok")

    def test_shops_app_has_no_models_or_migrations(self):
        shops_app = apps.get_app_config("shops")

        self.assertEqual(list(shops_app.get_models()), [])
        self.assertFalse((Path(shops_app.path) / "migrations").exists())

import unittest

from common.dtos import ServiceResponse
from common.errors import AccountApiUnavailable
from shops.use_cases import get_shop, save_shop
from tests.shops.fakes import FakeShopGateway


class ShopUseCaseTests(unittest.TestCase):
    def test_get_shop_delegates_and_returns_response(self):
        response = ServiceResponse(
            status_code=200,
            body={"name": "Mi tienda", "description": None},
        )
        gateway = FakeShopGateway(response=response)

        result = get_shop(gateway, "cookie")

        self.assertIs(result, response)
        self.assertEqual(gateway.calls, [("get_shop", "cookie")])

    def test_get_shop_forwards_missing_session(self):
        gateway = FakeShopGateway()

        get_shop(gateway, None)

        self.assertEqual(gateway.calls, [("get_shop", None)])

    def test_save_shop_forwards_arguments_verbatim(self):
        body = b'{"name":"Mi tienda","description":"Hola"}'
        gateway = FakeShopGateway()

        save_shop(gateway, "cookie", body, "application/json")

        self.assertEqual(
            gateway.calls,
            [("save_shop", "cookie", body, "application/json")],
        )
        self.assertIs(gateway.calls[0][2], body)

    def test_save_shop_preserves_body_bytes(self):
        body = b'{"name":"caf\xc3\xa9","description":null}'
        gateway = FakeShopGateway()

        save_shop(gateway, None, body, "application/json")

        forwarded = gateway.calls[0][2]
        self.assertEqual(forwarded, body)
        self.assertEqual(gateway.calls[0][1], None)

    def test_unavailable_error_is_propagated(self):
        gateway = FakeShopGateway(error=AccountApiUnavailable())

        with self.assertRaises(AccountApiUnavailable):
            get_shop(gateway, "cookie")

    def test_save_returns_gateway_response(self):
        response = ServiceResponse(status_code=200, body={"name": "Nueva"})
        gateway = FakeShopGateway(response=response)

        result = save_shop(gateway, "cookie", b"{}", "application/json")

        self.assertIs(result, response)

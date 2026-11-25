import unittest

from common.dtos import ServiceResponse
from common.ports import AccountApiGateway
from tests.shops.fakes import FakeShopGateway


class ShopPortsTests(unittest.TestCase):
    def test_fake_gateway_satisfies_account_api_gateway(self):
        gateway: AccountApiGateway = FakeShopGateway(
            response=ServiceResponse(status_code=200, body={"name": "Mi tienda"})
        )

        shop = gateway.get_shop("cookie")
        saved = gateway.save_shop("cookie", b'{"name":"Mi tienda"}', "application/json")

        self.assertIsInstance(shop, ServiceResponse)
        self.assertEqual(shop.status_code, 200)
        self.assertIsInstance(saved, ServiceResponse)
        self.assertEqual(saved.status_code, 200)

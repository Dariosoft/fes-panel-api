import unittest

from common.dtos import AccountLogout, AccountSession, ServiceResponse
from common.ports import AccountApiGateway, CatalogApiGateway


class FakeAccountApiGateway:
    def get_session(self, fes_session: str | None) -> AccountSession:
        if fes_session:
            return AccountSession(200, {"authenticated": True}, True, "acc-1")
        return AccountSession(200, {"authenticated": False}, False, None)

    def logout(self, fes_session: str | None) -> AccountLogout:
        raise AssertionError("logout should not be called")


class FakeCatalogGateway:
    def _response(self) -> ServiceResponse:
        return ServiceResponse(status_code=200, body={})

    def list_products(self, owner_account_id: str, name: str | None = None) -> ServiceResponse:
        return self._response()

    def create_product(
        self, owner_account_id: str, body: bytes, content_type: str | None
    ) -> ServiceResponse:
        return self._response()

    def update_product(
        self,
        owner_account_id: str,
        product_id: str,
        body: bytes,
        content_type: str | None,
    ) -> ServiceResponse:
        return self._response()

    def delete_product(self, owner_account_id: str, product_id: str) -> ServiceResponse:
        return self._response()

    def publish_product(self, owner_account_id: str, product_id: str) -> ServiceResponse:
        return self._response()

    def unpublish_product(self, owner_account_id: str, product_id: str) -> ServiceResponse:
        return self._response()

    def publish_catalog(
        self, owner_account_id: str, body: bytes, content_type: str | None
    ) -> ServiceResponse:
        return self._response()


class CatalogPortsTests(unittest.TestCase):
    def test_fakes_implement_ports(self):
        session_gateway: AccountApiGateway = FakeAccountApiGateway()
        catalog_gateway: CatalogApiGateway = FakeCatalogGateway()

        session = session_gateway.get_session("cookie")
        self.assertTrue(session.authenticated)
        self.assertEqual(session.account_id, "acc-1")

        response = catalog_gateway.list_products("acc-1")
        self.assertIsInstance(response, ServiceResponse)
        self.assertEqual(response.status_code, 200)

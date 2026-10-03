import unittest

from catalog.dtos import CatalogResponse, PanelSession
from catalog.ports import CatalogGateway, PanelSessionGateway


class FakePanelSessionGateway:
    def resolve(self, fes_session: str | None) -> PanelSession:
        if fes_session:
            return PanelSession(authenticated=True, account_id="acc-1")
        return PanelSession(authenticated=False, account_id=None)


class FakeCatalogGateway:
    def _response(self) -> CatalogResponse:
        return CatalogResponse(status_code=200, body={})

    def list_products(self, owner_account_id: str, name: str | None = None) -> CatalogResponse:
        return self._response()

    def create_product(
        self, owner_account_id: str, body: bytes, content_type: str | None
    ) -> CatalogResponse:
        return self._response()

    def update_product(
        self,
        owner_account_id: str,
        product_id: str,
        body: bytes,
        content_type: str | None,
    ) -> CatalogResponse:
        return self._response()

    def delete_product(self, owner_account_id: str, product_id: str) -> CatalogResponse:
        return self._response()

    def publish_product(self, owner_account_id: str, product_id: str) -> CatalogResponse:
        return self._response()

    def unpublish_product(self, owner_account_id: str, product_id: str) -> CatalogResponse:
        return self._response()

    def publish_catalog(
        self, owner_account_id: str, body: bytes, content_type: str | None
    ) -> CatalogResponse:
        return self._response()


class CatalogPortsTests(unittest.TestCase):
    def test_fakes_implement_ports(self):
        session_gateway: PanelSessionGateway = FakePanelSessionGateway()
        catalog_gateway: CatalogGateway = FakeCatalogGateway()

        session = session_gateway.resolve("cookie")
        self.assertTrue(session.authenticated)
        self.assertEqual(session.account_id, "acc-1")

        response = catalog_gateway.list_products("acc-1")
        self.assertIsInstance(response, CatalogResponse)
        self.assertEqual(response.status_code, 200)

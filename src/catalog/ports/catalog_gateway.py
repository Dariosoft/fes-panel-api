from typing import Protocol

from catalog.dtos import CatalogResponse


class CatalogGateway(Protocol):
    def list_products(self, owner_account_id: str, name: str | None = None) -> CatalogResponse:
        """List the products owned by the session account, optionally filtered by name."""

    def create_product(
        self,
        owner_account_id: str,
        body: bytes,
        content_type: str | None,
    ) -> CatalogResponse:
        """Create a product for the session account."""

    def update_product(
        self,
        owner_account_id: str,
        product_id: str,
        body: bytes,
        content_type: str | None,
    ) -> CatalogResponse:
        """Update a product owned by the session account."""

    def delete_product(self, owner_account_id: str, product_id: str) -> CatalogResponse:
        """Delete a product owned by the session account."""

    def publish_product(self, owner_account_id: str, product_id: str) -> CatalogResponse:
        """Publish a product owned by the session account."""

    def unpublish_product(self, owner_account_id: str, product_id: str) -> CatalogResponse:
        """Unpublish a product owned by the session account."""

    def publish_catalog(
        self,
        owner_account_id: str,
        body: bytes,
        content_type: str | None,
    ) -> CatalogResponse:
        """Publish the catalog set sent by the client for the session account."""

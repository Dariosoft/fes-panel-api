from typing import Protocol

from common.dtos import ServiceResponse


class CatalogApiGateway(Protocol):
    def list_products(self, owner_account_id: str, name: str | None = None) -> ServiceResponse:
        """List products owned by the session account, optionally filtered by name."""

    def create_product(
        self,
        owner_account_id: str,
        body: bytes,
        content_type: str | None,
    ) -> ServiceResponse:
        """Create a product for the session account."""

    def update_product(
        self,
        owner_account_id: str,
        product_id: str,
        body: bytes,
        content_type: str | None,
    ) -> ServiceResponse:
        """Update a product owned by the session account."""

    def delete_product(self, owner_account_id: str, product_id: str) -> ServiceResponse:
        """Delete a product owned by the session account."""

    def publish_product(self, owner_account_id: str, product_id: str) -> ServiceResponse:
        """Publish a product owned by the session account."""

    def unpublish_product(self, owner_account_id: str, product_id: str) -> ServiceResponse:
        """Unpublish a product owned by the session account."""

    def publish_catalog(
        self,
        owner_account_id: str,
        body: bytes,
        content_type: str | None,
    ) -> ServiceResponse:
        """Publish the catalog set sent by the client for the session account."""

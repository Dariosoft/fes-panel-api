from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from catalog.api.panel_session import PanelSessionGuardMixin
from catalog.use_cases import (
    list_products,
    create_product,
    update_product,
    delete_product,
    publish_product,
    unpublish_product
)


class PanelCatalogProductViewSet(PanelSessionGuardMixin, ViewSet):
    permission_classes = [AllowAny]
    authentication_classes = []

    def list(self, request: Request) -> Response:
        return self._forward(lambda gateway: list_products(gateway, self.owner_account_id))

    def create(self, request: Request) -> Response:
        return self._forward(
            lambda gateway: create_product(
                gateway,
                self.owner_account_id,
                request.body,
                request.content_type,
            )
        )

    def update(self, request: Request, product_id: str) -> Response:
        return self._forward(
            lambda gateway: update_product(
                gateway,
                self.owner_account_id,
                product_id,
                request.body,
                request.content_type,
            )
        )

    def destroy(self, request: Request, product_id: str) -> Response:
        return self._forward(
            lambda gateway: delete_product(gateway, self.owner_account_id, product_id)
        )

    def publish(self, request: Request, product_id: str) -> Response:
        return self._forward(
            lambda gateway: publish_product(gateway, self.owner_account_id, product_id)
        )

    def unpublish(self, request: Request, product_id: str) -> Response:
        return self._forward(
            lambda gateway: unpublish_product(gateway, self.owner_account_id, product_id)
        )

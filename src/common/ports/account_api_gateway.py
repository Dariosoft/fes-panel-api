from typing import Protocol

from common.dtos import AccountLogout, AccountSession, ServiceResponse


class AccountApiGateway(Protocol):
    def get_session(self, fes_session: str | None) -> AccountSession:
        """Fetch and interpret the shared session from the account API."""

    def logout(self, fes_session: str | None) -> AccountLogout:
        """Request logout of the shared session in the account API."""

    def get_shop(self, fes_session: str | None) -> ServiceResponse:
        """Fetch the current account shop from the account API."""

    def save_shop(
        self,
        fes_session: str | None,
        body: bytes,
        content_type: str | None,
    ) -> ServiceResponse:
        """Create or replace the current account shop in the account API."""

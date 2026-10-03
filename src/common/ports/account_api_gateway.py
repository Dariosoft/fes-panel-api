from typing import Protocol

from common.dtos import AccountLogout, AccountSession


class AccountApiGateway(Protocol):
    def get_session(self, fes_session: str | None) -> AccountSession:
        """Fetch and interpret the shared session from the account API."""

    def logout(self, fes_session: str | None) -> AccountLogout:
        """Request logout of the shared session in the account API."""

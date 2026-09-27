from typing import Protocol

from identity.application.dtos import LogoutResult, SessionPayload


class AccountSessionGateway(Protocol):
    def get_session(self, fes_session: str | None) -> SessionPayload:
        """Fetch the shared session payload from the accounts service."""

    def logout(self, fes_session: str | None) -> LogoutResult:
        """Request logout of the shared session in the accounts service."""

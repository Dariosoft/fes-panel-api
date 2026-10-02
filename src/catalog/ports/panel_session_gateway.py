from typing import Protocol

from catalog.dtos import PanelSession


class PanelSessionGateway(Protocol):
    def resolve(self, fes_session: str | None) -> PanelSession:
        """Resolve the shared panel session behind the fes_session cookie."""

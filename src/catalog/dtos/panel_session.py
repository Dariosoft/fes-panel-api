from dataclasses import dataclass


@dataclass(frozen=True)
class PanelSession:
    authenticated: bool
    account_id: str | None

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AccountSession:
    status_code: int
    body: dict[str, Any]
    authenticated: bool
    account_id: str | None

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AccountLogout:
    status_code: int
    body: dict[str, Any]
    had_active_session: bool

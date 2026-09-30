from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LogoutResult:
    status_code: int
    body: dict[str, Any]
    had_active_session: bool

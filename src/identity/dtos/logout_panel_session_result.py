from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LogoutPanelSessionResult:
    status_code: int
    body: dict[str, Any]
    clear_cookie: bool

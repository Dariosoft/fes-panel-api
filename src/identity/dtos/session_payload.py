from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SessionPayload:
    status_code: int
    body: dict[str, Any]

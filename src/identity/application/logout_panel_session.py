from dataclasses import dataclass
from typing import Any

from identity.application.ports import AccountSessionGateway
from identity.domain.errors import AccountServiceUnavailable


@dataclass(frozen=True)
class LogoutPanelSessionResult:
    status_code: int
    body: dict[str, Any]
    clear_cookie: bool


def logout_panel_session(
    gateway: AccountSessionGateway,
    fes_session: str | None,
) -> LogoutPanelSessionResult:
    try:
        result = gateway.logout(fes_session)
    except AccountServiceUnavailable:
        raise
    except Exception as exc:
        raise AccountServiceUnavailable from exc

    return LogoutPanelSessionResult(
        status_code=result.status_code,
        body=result.body,
        clear_cookie=True,
    )

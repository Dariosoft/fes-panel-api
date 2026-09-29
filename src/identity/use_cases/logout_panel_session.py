from identity.domain.errors import AccountServiceUnavailable
from identity.dtos import LogoutPanelSessionResult
from identity.ports import AccountSessionGateway


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

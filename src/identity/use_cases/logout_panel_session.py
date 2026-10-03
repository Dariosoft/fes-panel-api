from common.errors import AccountApiUnavailable
from common.ports import AccountApiGateway
from identity.dtos import LogoutPanelSessionResult


def logout_panel_session(
    gateway: AccountApiGateway,
    fes_session: str | None,
) -> LogoutPanelSessionResult:
    try:
        result = gateway.logout(fes_session)
    except AccountApiUnavailable:
        raise
    except Exception as exc:
        raise AccountApiUnavailable from exc

    return LogoutPanelSessionResult(
        status_code=result.status_code,
        body=result.body,
        clear_cookie=True,
    )

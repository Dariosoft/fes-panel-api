from common.errors import AccountApiUnavailable
from common.ports import AccountApiGateway


def resolve_panel_tenant(
    session_gateway: AccountApiGateway,
    fes_session: str | None,
) -> str | None:
    try:
        session = session_gateway.get_session(fes_session)
    except AccountApiUnavailable:
        raise
    except Exception as exc:
        raise AccountApiUnavailable from exc
    if not session.authenticated or not session.account_id:
        return None
    return session.account_id

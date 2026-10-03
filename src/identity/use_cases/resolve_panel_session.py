from common.dtos import AccountSession
from common.errors import AccountApiUnavailable
from common.ports import AccountApiGateway


def resolve_panel_session(
    gateway: AccountApiGateway,
    fes_session: str | None,
) -> AccountSession:
    try:
        return gateway.get_session(fes_session)
    except AccountApiUnavailable:
        raise
    except Exception as exc:
        raise AccountApiUnavailable from exc

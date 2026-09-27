from identity.application.dtos import SessionPayload
from identity.application.ports import AccountSessionGateway
from identity.domain.errors import AccountServiceUnavailable


def resolve_panel_session(
    gateway: AccountSessionGateway,
    fes_session: str | None,
) -> SessionPayload:
    try:
        return gateway.get_session(fes_session)
    except AccountServiceUnavailable:
        raise
    except Exception as exc:
        raise AccountServiceUnavailable from exc

from catalog.domain.errors import SessionServiceUnavailable
from catalog.dtos import PanelSession
from catalog.ports import PanelSessionGateway


def resolve_panel_owner(
    session_gateway: PanelSessionGateway,
    fes_session: str | None,
) -> PanelSession:
    try:
        return session_gateway.resolve(fes_session)
    except SessionServiceUnavailable:
        raise
    except Exception as exc:
        raise SessionServiceUnavailable from exc

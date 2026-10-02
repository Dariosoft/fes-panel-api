from catalog.domain.constants import SESSION_COOKIE_NAME
from catalog.domain.errors import SessionServiceUnavailable
from catalog.dtos import PanelSession
from common.contracts.account_api import (
    ACCOUNT_SESSION_PATH,
    SESSION_AUTHENTICATED_KEY,
    SESSION_ID_KEY,
)
from common.http import JsonRequest, RemoteServiceError, request_json


class AccountSessionClient:
    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def resolve(self, fes_session: str | None) -> PanelSession:
        headers: dict[str, str] = {}
        if fes_session:
            headers["Cookie"] = f"{SESSION_COOKIE_NAME}={fes_session}"
        call = JsonRequest("GET", ACCOUNT_SESSION_PATH, self._timeout_seconds, headers)
        try:
            _status_code, body = request_json(self._base_url, call)
        except RemoteServiceError as exc:
            raise SessionServiceUnavailable from exc

        account_id = body.get(SESSION_ID_KEY)
        return PanelSession(
            authenticated=bool(body.get(SESSION_AUTHENTICATED_KEY)),
            account_id=str(account_id) if account_id is not None else None,
        )

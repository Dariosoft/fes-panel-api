from common.contracts.account_api import ACCOUNT_LOGOUT_PATH, ACCOUNT_SESSION_PATH
from common.http import JsonRequest, RemoteServiceError, request_json
from identity.application.dtos import LogoutResult, SessionPayload
from identity.domain.constants import SESSION_COOKIE_NAME
from identity.domain.errors import AccountServiceUnavailable


class AccountSessionClient:
    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def get_session(self, fes_session: str | None) -> SessionPayload:
        status_code, body = self._request("GET", ACCOUNT_SESSION_PATH, fes_session)
        return SessionPayload(status_code=status_code, body=body)

    def logout(self, fes_session: str | None) -> LogoutResult:
        status_code, body = self._request("POST", ACCOUNT_LOGOUT_PATH, fes_session)
        return LogoutResult(
            status_code=status_code,
            body=body,
            had_active_session=bool(fes_session),
        )

    def _request(
        self,
        method: str,
        path: str,
        fes_session: str | None,
    ) -> tuple[int, dict]:
        headers: dict[str, str] = {}
        if fes_session:
            headers["Cookie"] = f"{SESSION_COOKIE_NAME}={fes_session}"
        call = JsonRequest(method, path, self._timeout_seconds, headers)
        try:
            return request_json(self._base_url, call)
        except RemoteServiceError as exc:
            raise AccountServiceUnavailable from exc

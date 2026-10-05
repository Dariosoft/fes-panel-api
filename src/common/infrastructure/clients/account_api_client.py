from typing import Any, cast

from common.contracts.account_api import (
    ACCOUNT_LOGOUT_PATH,
    ACCOUNT_SESSION_PATH,
    SESSION_AUTHENTICATED_KEY,
    SESSION_COOKIE_NAME,
    SESSION_ID_KEY,
)
from common.dtos import AccountLogout, AccountSession
from common.errors import AccountApiUnavailable
from common.http import JsonRequest, RemoteServiceError, request_json


class AccountApiClient:
    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def get_session(self, fes_session: str | None) -> AccountSession:
        status_code, response_body = self._request("GET", ACCOUNT_SESSION_PATH, fes_session)
        body = cast(dict[str, Any], response_body)
        account_id = body.get(SESSION_ID_KEY)
        return AccountSession(
            status_code=status_code,
            body=body,
            authenticated=bool(body.get(SESSION_AUTHENTICATED_KEY)),
            account_id=str(account_id) if account_id is not None else None,
        )

    def logout(self, fes_session: str | None) -> AccountLogout:
        status_code, response_body = self._request("POST", ACCOUNT_LOGOUT_PATH, fes_session)
        return AccountLogout(
            status_code=status_code,
            body=cast(dict[str, Any], response_body),
            had_active_session=bool(fes_session),
        )

    def _request(self, method: str, path: str, fes_session: str | None):
        headers: dict[str, str] = {}
        if fes_session:
            headers["Cookie"] = f"{SESSION_COOKIE_NAME}={fes_session}"
        call = JsonRequest(method, path, self._timeout_seconds, headers)
        try:
            return request_json(self._base_url, call)
        except RemoteServiceError as exc:
            raise AccountApiUnavailable from exc

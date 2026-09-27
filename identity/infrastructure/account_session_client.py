import json
import urllib.error
import urllib.request
from typing import Any

from identity.application.dtos import LogoutResult, SessionPayload
from identity.domain.constants import SESSION_COOKIE_NAME
from identity.domain.errors import AccountServiceUnavailable


class AccountSessionClient:
    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def get_session(self, fes_session: str | None) -> SessionPayload:
        status_code, body = self._request("GET", "/accounts/session", fes_session)
        return SessionPayload(status_code=status_code, body=body)

    def logout(self, fes_session: str | None) -> LogoutResult:
        status_code, body = self._request("POST", "/accounts/logout", fes_session)
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
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}{path}"
        headers: dict[str, str] = {"Accept": "application/json"}
        if fes_session:
            headers["Cookie"] = f"{SESSION_COOKIE_NAME}={fes_session}"
        request = urllib.request.Request(url, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
                status_code = response.getcode()
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            if exc.code >= 500:
                raise AccountServiceUnavailable from exc
            raw = exc.read().decode("utf-8")
            status_code = exc.code
        except (TimeoutError, urllib.error.URLError, OSError) as exc:
            raise AccountServiceUnavailable from exc

        try:
            body = json.loads(raw) if raw else {}
        except json.JSONDecodeError as exc:
            raise AccountServiceUnavailable from exc
        if not isinstance(body, dict):
            raise AccountServiceUnavailable("accounts response was not an object")
        return status_code, body

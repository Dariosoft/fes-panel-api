"""HTTP client for account-api (shared account and session owner)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from django.conf import settings

from identity.exceptions import AccountAccessRejected, AccountServiceUnavailable

SESSION_COOKIE_NAME = "fes_session"


@dataclass(frozen=True, slots=True)
class AccountIdentity:
    name: str
    email: str


@dataclass(frozen=True, slots=True)
class SessionResult:
    identity: AccountIdentity
    session_id: str


class AccountClient:
    """Typed client toward account-api. Does not own account tables."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        opener: Any | None = None,
    ) -> None:
        self.base_url = (base_url or settings.ACCOUNT_API_BASE_URL).rstrip("/")
        self.timeout_seconds = (
            timeout_seconds if timeout_seconds is not None else settings.ACCOUNT_API_TIMEOUT_SECONDS
        )
        self._opener = opener or urllib.request.urlopen

    def confirm_google_access(self, credential: str) -> SessionResult:
        """Confirm Google access and open the shared session."""
        payload = self._request_json(
            "POST",
            "/accounts/session/google",
            body={"provider": "google", "credential": credential},
            expected_ok=frozenset({200, 201}),
        )
        return self._parse_session_result(payload)

    def get_identity(self, session_id: str | None) -> AccountIdentity | None:
        """Return current identity for the shared session, or None if anonymous."""
        if not session_id:
            return None
        try:
            payload = self._request_json(
                "GET",
                "/accounts/me",
                session_id=session_id,
                expected_ok=frozenset({200}),
                allow_unauthorized=True,
            )
        except AccountAccessRejected:
            return None
        if payload is None:
            return None
        if payload.get("authenticated") is False:
            return None
        return self._parse_identity(payload)

    def close_session(self, session_id: str | None) -> None:
        """Close the shared session. Idempotent when already anonymous."""
        self._request_json(
            "POST",
            "/accounts/session/logout",
            session_id=session_id,
            expected_ok=frozenset({200, 204}),
            allow_unauthorized=True,
        )

    def _parse_session_result(self, payload: dict[str, Any]) -> SessionResult:
        session_id = payload.get("session_id") or payload.get("sessionId")
        if not session_id or not isinstance(session_id, str):
            raise AccountServiceUnavailable("account-api no devolvió sesión")
        return SessionResult(identity=self._parse_identity(payload), session_id=session_id)

    def _parse_identity(self, payload: dict[str, Any]) -> AccountIdentity:
        name = payload.get("name") or payload.get("display_name")
        email = payload.get("email")
        if not name or not email:
            raise AccountServiceUnavailable("account-api no devolvió identidad completa")
        return AccountIdentity(name=str(name), email=str(email))

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        session_id: str | None = None,
        expected_ok: frozenset[int],
        allow_unauthorized: bool = False,
    ) -> dict[str, Any] | None:
        url = f"{self.base_url}{path}"
        data = None if body is None else json.dumps(body).encode("utf-8")
        headers = {"Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        if session_id:
            headers["Cookie"] = f"{SESSION_COOKIE_NAME}={session_id}"
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with self._opener(request, timeout=self.timeout_seconds) as response:
                status = getattr(response, "status", None) or response.getcode()
                raw = response.read()
        except TimeoutError as exc:
            raise AccountServiceUnavailable("account-api no respondió a tiempo") from exc
        except urllib.error.HTTPError as exc:
            return self._map_http_error(exc, allow_unauthorized=allow_unauthorized)
        except urllib.error.URLError as exc:
            raise AccountServiceUnavailable("account-api no está disponible") from exc
        except OSError as exc:
            raise AccountServiceUnavailable("account-api no está disponible") from exc

        if status >= 500:
            raise AccountServiceUnavailable("account-api respondió con error interno")
        if status in (401, 403):
            if allow_unauthorized:
                return None
            raise AccountAccessRejected("acceso rechazado por el sistema de cuentas")
        if status not in expected_ok:
            if 400 <= status < 500:
                raise AccountAccessRejected("acceso rechazado por el sistema de cuentas")
            raise AccountServiceUnavailable("account-api respondió de forma inesperada")
        if not raw:
            return {}
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AccountServiceUnavailable("account-api devolvió una respuesta inválida") from exc
        if not isinstance(parsed, dict):
            raise AccountServiceUnavailable("account-api devolvió una respuesta inválida")
        return parsed

    def _map_http_error(
        self,
        exc: urllib.error.HTTPError,
        *,
        allow_unauthorized: bool,
    ) -> dict[str, Any] | None:
        status = exc.code
        if status >= 500:
            raise AccountServiceUnavailable("account-api respondió con error interno") from exc
        if status in (401, 403):
            if allow_unauthorized:
                return None
            raise AccountAccessRejected("acceso rechazado por el sistema de cuentas") from exc
        if 400 <= status < 500:
            raise AccountAccessRejected("acceso rechazado por el sistema de cuentas") from exc
        raise AccountServiceUnavailable("account-api respondió de forma inesperada") from exc

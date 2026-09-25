"""Domain services for panel identity (login / logout / whoami)."""

from __future__ import annotations

from dataclasses import dataclass

from identity.account_client import AccountClient, AccountIdentity, SessionResult


@dataclass(frozen=True, slots=True)
class WhoAmIResult:
    authenticated: bool
    name: str | None = None
    email: str | None = None


@dataclass(frozen=True, slots=True)
class LoginResult:
    authenticated: bool
    name: str
    email: str
    session_id: str


class IdentityService:
    """Orchestrates identity operations via account-api. No local account tables."""

    def __init__(self, client: AccountClient | None = None) -> None:
        self._client = client or AccountClient()

    def login_with_google(self, credential: str) -> LoginResult:
        session: SessionResult = self._client.confirm_google_access(credential)
        return LoginResult(
            authenticated=True,
            name=session.identity.name,
            email=session.identity.email,
            session_id=session.session_id,
        )

    def logout(self, session_id: str | None) -> None:
        self._client.close_session(session_id)

    def whoami(self, session_id: str | None) -> WhoAmIResult:
        identity: AccountIdentity | None = self._client.get_identity(session_id)
        if identity is None:
            return WhoAmIResult(authenticated=False)
        return WhoAmIResult(authenticated=True, name=identity.name, email=identity.email)

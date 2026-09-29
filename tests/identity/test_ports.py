import unittest

from identity.dtos import LogoutResult, SessionPayload
from identity.ports import AccountSessionGateway


class FakeAccountSessionGateway:
    def get_session(self, fes_session: str | None) -> SessionPayload:
        if fes_session:
            return SessionPayload(
                status_code=200,
                body={"authenticated": True, "id": "1", "email": "a@b.c", "name": "A"},
            )
        return SessionPayload(status_code=200, body={"authenticated": False})

    def logout(self, fes_session: str | None) -> LogoutResult:
        return LogoutResult(
            status_code=200,
            body={"authenticated": False},
            had_active_session=bool(fes_session),
        )


class AccountSessionGatewayTests(unittest.TestCase):
    def test_fake_implements_port(self):
        gateway: AccountSessionGateway = FakeAccountSessionGateway()
        session = gateway.get_session("token")
        self.assertTrue(session.body["authenticated"])
        logout = gateway.logout(None)
        self.assertFalse(logout.body["authenticated"])
        self.assertFalse(logout.had_active_session)

import unittest

from common.dtos import AccountLogout, AccountSession
from common.ports import AccountApiGateway


class FakeAccountApiGateway:
    def get_session(self, fes_session: str | None) -> AccountSession:
        if fes_session:
            return AccountSession(
                status_code=200,
                body={"authenticated": True, "id": "1", "email": "a@b.c", "name": "A"},
                authenticated=True,
                account_id="1",
            )
        return AccountSession(
            status_code=200,
            body={"authenticated": False},
            authenticated=False,
            account_id=None,
        )

    def logout(self, fes_session: str | None) -> AccountLogout:
        return AccountLogout(
            status_code=200,
            body={"authenticated": False},
            had_active_session=bool(fes_session),
        )


class AccountApiGatewayTests(unittest.TestCase):
    def test_fake_implements_port(self):
        gateway: AccountApiGateway = FakeAccountApiGateway()
        session = gateway.get_session("token")
        self.assertTrue(session.body["authenticated"])
        logout = gateway.logout(None)
        self.assertFalse(logout.body["authenticated"])
        self.assertFalse(logout.had_active_session)

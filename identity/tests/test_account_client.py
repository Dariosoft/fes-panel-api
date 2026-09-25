import io
import json
import urllib.error
from unittest.mock import MagicMock

from django.test import SimpleTestCase

from identity.account_client import AccountClient
from identity.exceptions import AccountAccessRejected, AccountServiceUnavailable


def _response(payload: dict | None, *, status: int = 200):
    body = b"" if payload is None else json.dumps(payload).encode("utf-8")
    response = MagicMock()
    response.status = status
    response.getcode.return_value = status
    response.read.return_value = body
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


class AccountClientTests(SimpleTestCase):
    def setUp(self):
        self.opener = MagicMock()
        self.client = AccountClient(
            base_url="http://accounts.test",
            timeout_seconds=1.0,
            opener=self.opener,
        )

    def test_confirm_google_access_success(self):
        self.opener.return_value = _response(
            {
                "name": "Ada Lovelace",
                "email": "ada@example.com",
                "session_id": "sess-1",
            }
        )
        result = self.client.confirm_google_access("google-credential")
        self.assertEqual(result.identity.name, "Ada Lovelace")
        self.assertEqual(result.identity.email, "ada@example.com")
        self.assertEqual(result.session_id, "sess-1")
        request = self.opener.call_args.args[0]
        self.assertEqual(request.full_url, "http://accounts.test/accounts/session/google")
        self.assertEqual(request.get_method(), "POST")

    def test_confirm_google_access_rejects_business_error(self):
        self.opener.side_effect = urllib.error.HTTPError(
            url="http://accounts.test/accounts/session/google",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=io.BytesIO(b'{"message":"rechazado"}'),
        )
        with self.assertRaises(AccountAccessRejected):
            self.client.confirm_google_access("bad-credential")

    def test_confirm_google_access_maps_timeout_to_unavailable(self):
        self.opener.side_effect = TimeoutError()
        with self.assertRaises(AccountServiceUnavailable):
            self.client.confirm_google_access("google-credential")

    def test_confirm_google_access_maps_5xx_to_unavailable(self):
        self.opener.side_effect = urllib.error.HTTPError(
            url="http://accounts.test/accounts/session/google",
            code=503,
            msg="Unavailable",
            hdrs=None,
            fp=io.BytesIO(b""),
        )
        with self.assertRaises(AccountServiceUnavailable):
            self.client.confirm_google_access("google-credential")

    def test_get_identity_authenticated(self):
        self.opener.return_value = _response(
            {"name": "Ada Lovelace", "email": "ada@example.com", "authenticated": True}
        )
        identity = self.client.get_identity("sess-1")
        self.assertIsNotNone(identity)
        assert identity is not None
        self.assertEqual(identity.email, "ada@example.com")

    def test_get_identity_anonymous_when_unauthorized(self):
        self.opener.side_effect = urllib.error.HTTPError(
            url="http://accounts.test/accounts/me",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=io.BytesIO(b""),
        )
        self.assertIsNone(self.client.get_identity("sess-missing"))

    def test_close_session_idempotent(self):
        self.opener.return_value = _response({}, status=204)
        self.client.close_session("sess-1")
        request = self.opener.call_args.args[0]
        self.assertEqual(request.full_url, "http://accounts.test/accounts/session/logout")
        self.assertEqual(request.get_method(), "POST")

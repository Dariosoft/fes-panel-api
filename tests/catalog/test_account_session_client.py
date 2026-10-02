import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from catalog.domain import SESSION_COOKIE_NAME, SessionServiceUnavailable
from catalog.infrastructure.account_session_client import AccountSessionClient


class _Handler(BaseHTTPRequestHandler):
    status = 200
    body: dict = {"authenticated": False}
    last_cookie: str | None = None
    last_path: str | None = None

    def log_message(self, *args) -> None:
        return

    def do_GET(self) -> None:
        _Handler.last_cookie = self.headers.get("Cookie")
        _Handler.last_path = self.path
        payload = json.dumps(_Handler.body).encode("utf-8")
        self.send_response(_Handler.status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class AccountSessionClientTests(unittest.TestCase):
    def setUp(self):
        _Handler.status = 200
        _Handler.body = {"authenticated": False}
        _Handler.last_cookie = None
        _Handler.last_path = None
        self.server = HTTPServer(("127.0.0.1", 0), _Handler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.client = AccountSessionClient(f"http://127.0.0.1:{self.port}", timeout_seconds=2)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def test_resolves_authenticated_session_from_base_url_and_cookie(self):
        _Handler.body = {"authenticated": True, "id": "acc-9"}

        session = self.client.resolve("abc")

        self.assertTrue(session.authenticated)
        self.assertEqual(session.account_id, "acc-9")
        self.assertEqual(_Handler.last_path, "/accounts/session")
        self.assertEqual(_Handler.last_cookie, f"{SESSION_COOKIE_NAME}=abc")

    def test_anonymous_session_has_no_account(self):
        _Handler.body = {"authenticated": False}

        session = self.client.resolve(None)

        self.assertFalse(session.authenticated)
        self.assertIsNone(session.account_id)
        self.assertIsNone(_Handler.last_cookie)

    def test_numeric_id_is_normalized_to_string(self):
        _Handler.body = {"authenticated": True, "id": 9}

        session = self.client.resolve("abc")

        self.assertEqual(session.account_id, "9")

    def test_server_error_maps_to_unavailable(self):
        _Handler.status = 503
        _Handler.body = {"error": "down"}

        with self.assertRaises(SessionServiceUnavailable):
            self.client.resolve("x")

    def test_connection_failure_maps_to_unavailable(self):
        self.server.shutdown()
        broken = AccountSessionClient(f"http://127.0.0.1:{self.port}", timeout_seconds=0.5)

        with self.assertRaises(SessionServiceUnavailable):
            broken.resolve("x")

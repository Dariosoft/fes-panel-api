import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from common.contracts.account_api import SESSION_COOKIE_NAME
from common.errors import AccountApiUnavailable
from common.infrastructure.clients import AccountApiClient


class _Handler(BaseHTTPRequestHandler):
    responses: dict[str, tuple[int, dict]] = {}
    last_cookie: str | None = None
    last_path: str | None = None

    def log_message(self, *args) -> None:
        return

    def do_GET(self) -> None:
        self._handle("GET")

    def do_POST(self) -> None:
        self._handle("POST")

    def _handle(self, method: str) -> None:
        _Handler.last_cookie = self.headers.get("Cookie")
        _Handler.last_path = self.path
        key = f"{method} {self.path}"
        status, body = _Handler.responses.get(key, (200, {"authenticated": False}))
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class AccountApiClientTests(unittest.TestCase):
    def setUp(self):
        _Handler.responses = {}
        _Handler.last_cookie = None
        _Handler.last_path = None
        self.server = HTTPServer(("127.0.0.1", 0), _Handler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.client = AccountApiClient(f"http://127.0.0.1:{self.port}", timeout_seconds=2)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def test_get_session_forwards_cookie_and_base_url(self):
        body = {"authenticated": True, "id": "1", "email": "a@b.c", "name": "A"}
        _Handler.responses["GET /accounts/session"] = (200, body)
        result = self.client.get_session("abc")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.body, body)
        self.assertTrue(result.authenticated)
        self.assertEqual(result.account_id, "1")
        self.assertEqual(_Handler.last_path, "/accounts/session")
        self.assertEqual(_Handler.last_cookie, f"{SESSION_COOKIE_NAME}=abc")

    def test_logout_forwards_cookie(self):
        _Handler.responses["POST /accounts/logout"] = (200, {"authenticated": False})
        result = self.client.logout("tok")
        self.assertEqual(result.body, {"authenticated": False})
        self.assertEqual(_Handler.last_path, "/accounts/logout")
        self.assertEqual(_Handler.last_cookie, f"{SESSION_COOKIE_NAME}=tok")

    def test_numeric_account_id_is_normalized_to_string(self):
        _Handler.responses["GET /accounts/session"] = (200, {"authenticated": True, "id": 9})

        result = self.client.get_session("abc")

        self.assertEqual(result.account_id, "9")

    def test_anonymous_session_omits_cookie_and_account(self):
        result = self.client.get_session(None)

        self.assertFalse(result.authenticated)
        self.assertIsNone(result.account_id)
        self.assertIsNone(_Handler.last_cookie)

    def test_server_error_maps_to_unavailable(self):
        _Handler.responses["GET /accounts/session"] = (503, {"error": "down"})
        with self.assertRaises(AccountApiUnavailable):
            self.client.get_session("x")

    def test_connection_failure_maps_to_unavailable(self):
        self.server.shutdown()
        broken = AccountApiClient(f"http://127.0.0.1:{self.port}", timeout_seconds=0.5)
        with self.assertRaises(AccountApiUnavailable):
            broken.get_session("x")

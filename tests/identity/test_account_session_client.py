import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from identity.domain import SESSION_COOKIE_NAME, AccountServiceUnavailable
from identity.infrastructure.account_session_client import AccountSessionClient


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


class AccountSessionClientTests(unittest.TestCase):
    def setUp(self):
        _Handler.responses = {}
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

    def test_get_session_forwards_cookie_and_base_url(self):
        body = {"authenticated": True, "id": "1", "email": "a@b.c", "name": "A"}
        _Handler.responses["GET /accounts/session"] = (200, body)
        result = self.client.get_session("abc")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.body, body)
        self.assertEqual(_Handler.last_path, "/accounts/session")
        self.assertEqual(_Handler.last_cookie, f"{SESSION_COOKIE_NAME}=abc")

    def test_logout_forwards_cookie(self):
        _Handler.responses["POST /accounts/logout"] = (200, {"authenticated": False})
        result = self.client.logout("tok")
        self.assertEqual(result.body, {"authenticated": False})
        self.assertEqual(_Handler.last_path, "/accounts/logout")
        self.assertEqual(_Handler.last_cookie, f"{SESSION_COOKIE_NAME}=tok")

    def test_server_error_maps_to_unavailable(self):
        _Handler.responses["GET /accounts/session"] = (503, {"error": "down"})
        with self.assertRaises(AccountServiceUnavailable):
            self.client.get_session("x")

    def test_connection_failure_maps_to_unavailable(self):
        self.server.shutdown()
        broken = AccountSessionClient(f"http://127.0.0.1:{self.port}", timeout_seconds=0.5)
        with self.assertRaises(AccountServiceUnavailable):
            broken.get_session("x")

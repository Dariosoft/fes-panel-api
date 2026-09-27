import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from common.http import JsonRequest, RemoteServiceError, request_json


class _Handler(BaseHTTPRequestHandler):
    status = 200
    raw = b"{}"
    trace: str | None = None
    accept: str | None = None

    def log_message(self, *args) -> None:
        return

    def do_GET(self) -> None:
        _Handler.trace = self.headers.get("X-Trace")
        _Handler.accept = self.headers.get("Accept")
        payload = _Handler.raw
        self.send_response(_Handler.status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class RequestJsonTests(unittest.TestCase):
    def setUp(self):
        _Handler.status = 200
        _Handler.raw = b"{}"
        _Handler.trace = None
        _Handler.accept = None
        self.server = HTTPServer(("127.0.0.1", 0), _Handler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def test_returns_json_object_and_sends_caller_headers(self):
        _Handler.raw = json.dumps({"ok": True}).encode("utf-8")
        call = JsonRequest("GET", "/catalog/products", 2, {"X-Trace": "1"})

        status_code, body = request_json(self.base_url, call)

        self.assertEqual(status_code, 200)
        self.assertEqual(body, {"ok": True})
        self.assertEqual(_Handler.trace, "1")
        self.assertEqual(_Handler.accept, "application/json")

    def test_returns_client_error_body(self):
        _Handler.status = 404
        _Handler.raw = json.dumps({"missing": True}).encode("utf-8")
        call = JsonRequest("GET", "/missing", 2)

        status_code, body = request_json(self.base_url, call)

        self.assertEqual(status_code, 404)
        self.assertEqual(body, {"missing": True})

    def test_server_error_is_remote_failure(self):
        _Handler.status = 503
        _Handler.raw = json.dumps({"error": "down"}).encode("utf-8")
        call = JsonRequest("GET", "/down", 2)

        with self.assertRaises(RemoteServiceError):
            request_json(self.base_url, call)

    def test_json_array_is_remote_failure(self):
        _Handler.raw = b"[1]"
        call = JsonRequest("GET", "/list", 2)

        with self.assertRaises(RemoteServiceError):
            request_json(self.base_url, call)

    def test_invalid_json_is_remote_failure(self):
        _Handler.raw = b"not-json"
        call = JsonRequest("GET", "/bad", 2)

        with self.assertRaises(RemoteServiceError):
            request_json(self.base_url, call)

    def test_connection_failure_is_remote_failure(self):
        self.server.shutdown()
        call = JsonRequest("GET", "/gone", 0.5)

        with self.assertRaises(RemoteServiceError):
            request_json(self.base_url, call)

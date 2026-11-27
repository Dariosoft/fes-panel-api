import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from common.errors import NotificationsApiTimeout, NotificationsApiUnavailable
from common.infrastructure.clients import NotificationsApiClient


class _Handler(BaseHTTPRequestHandler):
    status = 200
    chunks: list[bytes] = [b"data: one\n\n", b"data: two\n\n"]
    last_path: str | None = None
    last_query: dict | None = None
    last_accept: str | None = None

    def log_message(self, *args) -> None:
        return

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        _Handler.last_path = parsed.path
        _Handler.last_query = parse_qs(parsed.query)
        _Handler.last_accept = self.headers.get("Accept")
        self.send_response(_Handler.status)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for chunk in _Handler.chunks:
            self.wfile.write(chunk)
            self.wfile.flush()


class NotificationsApiClientTests(unittest.TestCase):
    def setUp(self):
        _Handler.status = 200
        _Handler.chunks = [b"data: one\n\n", b"data: two\n\n"]
        _Handler.last_path = None
        _Handler.last_query = None
        _Handler.last_accept = None
        self.server = HTTPServer(("127.0.0.1", 0), _Handler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.client = NotificationsApiClient(f"http://127.0.0.1:{self.port}")

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def test_open_feed_streams_upstream_payload(self):
        upstream = self.client.open_feed("tenant-1")
        try:
            payload = upstream.read()
        finally:
            upstream.close()

        self.assertEqual(payload, b"data: one\n\ndata: two\n\n")
        self.assertEqual(_Handler.last_path, "/notifications/feed")
        self.assertEqual(_Handler.last_query["tenantId"], ["tenant-1"])
        self.assertEqual(_Handler.last_accept, "text/event-stream")

    def test_upstream_error_maps_to_unavailable(self):
        _Handler.status = 503

        with self.assertRaises(NotificationsApiUnavailable):
            self.client.open_feed("tenant-1")

    def test_connection_failure_maps_to_unavailable(self):
        self.server.shutdown()
        self.server.server_close()
        broken = NotificationsApiClient(f"http://127.0.0.1:{self.port}")

        with self.assertRaises(NotificationsApiUnavailable):
            broken.open_feed("tenant-1")

    def test_timeout_maps_to_timeout_error(self):
        with (
            patch(
                "common.infrastructure.clients.notifications_api_client.urllib.request.urlopen",
                side_effect=TimeoutError,
            ),
            self.assertRaises(NotificationsApiTimeout),
        ):
            self.client.open_feed("tenant-1")

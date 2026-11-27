import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from common.errors import AnalyticsApiTimeout, AnalyticsApiUnavailable
from common.http import RemoteServiceError
from common.infrastructure.clients import AnalyticsApiClient


class _Handler(BaseHTTPRequestHandler):
    status = 200
    body: dict = {}
    last_path: str | None = None
    last_query: dict | None = None

    def log_message(self, *args) -> None:
        return

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        _Handler.last_path = parsed.path
        _Handler.last_query = parse_qs(parsed.query)
        payload = json.dumps(_Handler.body).encode("utf-8")
        self.send_response(_Handler.status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class AnalyticsApiClientTests(unittest.TestCase):
    def setUp(self):
        _Handler.status = 200
        _Handler.body = {}
        _Handler.last_path = None
        _Handler.last_query = None
        self.server = HTTPServer(("127.0.0.1", 0), _Handler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.client = AnalyticsApiClient(f"http://127.0.0.1:{self.port}", timeout_seconds=2)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def test_timeline_uses_path_and_tenant(self):
        _Handler.body = {"events": []}

        result = self.client.timeline("tenant-1")

        self.assertEqual(_Handler.last_path, "/analytics/timeline")
        self.assertEqual(_Handler.last_query["tenantId"], ["tenant-1"])
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.body, {"events": []})

    def test_timeline_includes_order_filter(self):
        self.client.timeline("tenant-1", "order-9")

        self.assertEqual(_Handler.last_query["tenantId"], ["tenant-1"])
        self.assertEqual(_Handler.last_query["orderId"], ["order-9"])

    def test_metrics_uses_metrics_path_and_tenant(self):
        _Handler.body = {"orders": 3}

        result = self.client.metrics("tenant-1")

        self.assertEqual(_Handler.last_path, "/analytics/metrics")
        self.assertEqual(_Handler.last_query["tenantId"], ["tenant-1"])
        self.assertEqual(result.body, {"orders": 3})

    def test_client_error_is_proxied_with_status_and_body(self):
        _Handler.status = 422
        _Handler.body = {"error": "invalid"}

        result = self.client.metrics("tenant-1")

        self.assertEqual(result.status_code, 422)
        self.assertEqual(result.body, {"error": "invalid"})

    def test_server_error_maps_to_unavailable(self):
        _Handler.status = 503

        with self.assertRaises(AnalyticsApiUnavailable):
            self.client.metrics("tenant-1")

    def test_connection_failure_maps_to_unavailable(self):
        self.server.shutdown()
        broken = AnalyticsApiClient(f"http://127.0.0.1:{self.port}", timeout_seconds=0.5)

        with self.assertRaises(AnalyticsApiUnavailable):
            broken.timeline("tenant-1")

    def test_timeout_maps_to_timeout_error(self):
        def _raise_timeout(*args, **kwargs):
            raise RemoteServiceError from TimeoutError()

        with (
            patch(
                "common.infrastructure.clients.analytics_api_client.request_json",
                side_effect=_raise_timeout,
            ),
            self.assertRaises(AnalyticsApiTimeout),
        ):
            self.client.timeline("tenant-1")

    def test_remote_failure_maps_to_unavailable(self):
        with (
            patch(
                "common.infrastructure.clients.analytics_api_client.request_json",
                side_effect=RemoteServiceError,
            ),
            self.assertRaises(AnalyticsApiUnavailable),
        ):
            self.client.metrics("tenant-1")

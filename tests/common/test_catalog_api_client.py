import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from common.errors import CatalogApiUnavailable
from common.infrastructure.clients import CatalogApiClient


class _Handler(BaseHTTPRequestHandler):
    status = 200
    body: dict = {}
    last_method: str | None = None
    last_path: str | None = None
    last_query: dict | None = None
    last_body: bytes | None = None
    last_content_type: str | None = None

    def log_message(self, *args) -> None:
        return

    def do_GET(self) -> None:
        self._respond("GET")

    def do_POST(self) -> None:
        self._respond("POST")

    def do_PUT(self) -> None:
        self._respond("PUT")

    def do_DELETE(self) -> None:
        self._respond("DELETE")

    def _respond(self, method: str) -> None:
        parsed = urlparse(self.path)
        _Handler.last_method = method
        _Handler.last_path = parsed.path
        _Handler.last_query = parse_qs(parsed.query)
        _Handler.last_content_type = self.headers.get("Content-Type")
        length = int(self.headers.get("Content-Length") or 0)
        _Handler.last_body = self.rfile.read(length) if length else b""
        payload = json.dumps(_Handler.body).encode("utf-8")
        self.send_response(_Handler.status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class CatalogApiClientTests(unittest.TestCase):
    def setUp(self):
        _Handler.status = 200
        _Handler.body = {}
        _Handler.last_method = None
        _Handler.last_path = None
        _Handler.last_query = None
        _Handler.last_body = None
        _Handler.last_content_type = None
        self.server = HTTPServer(("127.0.0.1", 0), _Handler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.client = CatalogApiClient(f"http://127.0.0.1:{self.port}", timeout_seconds=2)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def test_list_products_uses_collection_path_and_session_owner(self):
        _Handler.body = {"items": []}

        result = self.client.list_products("acc-1")

        self.assertEqual(_Handler.last_method, "GET")
        self.assertEqual(_Handler.last_path, "/catalog/products")
        self.assertEqual(_Handler.last_query["ownerAccountId"], ["acc-1"])
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.body, {"items": []})

    def test_list_products_includes_name_filter(self):
        _Handler.body = {"items": []}

        self.client.list_products("acc-1", "mat")

        self.assertEqual(_Handler.last_query["ownerAccountId"], ["acc-1"])
        self.assertEqual(_Handler.last_query["name"], ["mat"])

    def test_create_product_forwards_body_and_content_type(self):
        raw_body = b'{"name":"camisa","ownerAccountId":"otro"}'
        _Handler.body = {"id": "p1"}

        result = self.client.create_product("acc-1", raw_body, "application/json")

        self.assertEqual(_Handler.last_method, "POST")
        self.assertEqual(_Handler.last_path, "/catalog/products")
        self.assertEqual(_Handler.last_query["ownerAccountId"], ["acc-1"])
        self.assertEqual(_Handler.last_body, raw_body)
        self.assertEqual(_Handler.last_content_type, "application/json")
        self.assertEqual(result.body, {"id": "p1"})

    def test_update_product_uses_item_path(self):
        raw_body = b'{"name":"nueva"}'

        self.client.update_product("acc-1", "p9", raw_body, "application/json")

        self.assertEqual(_Handler.last_method, "PUT")
        self.assertEqual(_Handler.last_path, "/catalog/products/p9")
        self.assertEqual(_Handler.last_query["ownerAccountId"], ["acc-1"])
        self.assertEqual(_Handler.last_body, raw_body)

    def test_delete_product_uses_item_path(self):
        self.client.delete_product("acc-1", "p9")

        self.assertEqual(_Handler.last_method, "DELETE")
        self.assertEqual(_Handler.last_path, "/catalog/products/p9")
        self.assertEqual(_Handler.last_query["ownerAccountId"], ["acc-1"])

    def test_publish_and_unpublish_product_paths(self):
        self.client.publish_product("acc-1", "p9")
        self.assertEqual(_Handler.last_method, "POST")
        self.assertEqual(_Handler.last_path, "/catalog/products/p9/publish")
        self.assertEqual(_Handler.last_query["ownerAccountId"], ["acc-1"])

        self.client.unpublish_product("acc-1", "p9")
        self.assertEqual(_Handler.last_path, "/catalog/products/p9/unpublish")
        self.assertEqual(_Handler.last_query["ownerAccountId"], ["acc-1"])

    def test_publish_catalog_forwards_body(self):
        raw_body = b'{"products":[]}'

        self.client.publish_catalog("acc-1", raw_body, "application/json")

        self.assertEqual(_Handler.last_method, "POST")
        self.assertEqual(_Handler.last_path, "/catalog/publish")
        self.assertEqual(_Handler.last_query["ownerAccountId"], ["acc-1"])
        self.assertEqual(_Handler.last_body, raw_body)

    def test_client_error_is_proxied_with_status_and_body(self):
        _Handler.status = 422
        _Handler.body = {"error": "invalid", "message": "Campos inválidos"}

        result = self.client.create_product("acc-1", b"{}", "application/json")

        self.assertEqual(result.status_code, 422)
        self.assertEqual(result.body, {"error": "invalid", "message": "Campos inválidos"})

    def test_body_owner_never_replaces_session_owner_in_query(self):
        raw_body = b'{"ownerAccountId":"intruso"}'

        self.client.publish_catalog("acc-session", raw_body, "application/json")

        self.assertEqual(_Handler.last_query["ownerAccountId"], ["acc-session"])
        self.assertEqual(_Handler.last_body, raw_body)

    def test_server_error_maps_to_unavailable(self):
        _Handler.status = 503

        with self.assertRaises(CatalogApiUnavailable):
            self.client.list_products("acc-1")

    def test_connection_failure_maps_to_unavailable(self):
        self.server.shutdown()
        broken = CatalogApiClient(f"http://127.0.0.1:{self.port}", timeout_seconds=0.5)

        with self.assertRaises(CatalogApiUnavailable):
            broken.list_products("acc-1")

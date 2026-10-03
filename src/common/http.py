import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field

from common.json_types import JsonBody


class RemoteServiceError(Exception):
    """The remote service did not return a usable JSON object or array."""


@dataclass(frozen=True)
class JsonRequest:
    method: str
    path: str
    timeout_seconds: float
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes | None = None
    content_type: str | None = None


def request_json(base_url: str, call: JsonRequest) -> tuple[int, JsonBody]:
    url = f"{base_url.rstrip('/')}{call.path}"
    headers = {"Accept": "application/json", **call.headers}
    if call.content_type:
        headers["Content-Type"] = call.content_type
    try:
        status_code, raw = _read_body(url, call.method, headers, call.timeout_seconds, call.body)
    except urllib.error.HTTPError as exc:
        if exc.code >= 500:
            raise RemoteServiceError from exc
        status_code = exc.code
        raw = exc.read().decode("utf-8")
    except (TimeoutError, urllib.error.URLError, OSError) as exc:
        raise RemoteServiceError from exc
    return status_code, _json_body(raw)


def _read_body(
    url: str,
    method: str,
    headers: dict[str, str],
    timeout_seconds: float,
    body: bytes | None = None,
) -> tuple[int, str]:
    request = urllib.request.Request(url, data=body, method=method, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        return response.getcode(), response.read().decode("utf-8")


def _json_body(raw: str) -> JsonBody:
    try:
        body = json.loads(raw) if raw else {}
    except json.JSONDecodeError as exc:
        raise RemoteServiceError from exc
    if not isinstance(body, (dict, list)):
        raise RemoteServiceError("response was not an object or array")
    return body

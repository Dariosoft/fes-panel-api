import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any


class RemoteServiceError(Exception):
    """The remote service did not return a usable JSON object."""


@dataclass(frozen=True)
class JsonRequest:
    method: str
    path: str
    timeout_seconds: float
    headers: dict[str, str] = field(default_factory=dict)


def request_json(base_url: str, call: JsonRequest) -> tuple[int, dict[str, Any]]:
    url = f"{base_url.rstrip('/')}{call.path}"
    headers = {"Accept": "application/json", **call.headers}
    try:
        status_code, raw = _read_body(url, call.method, headers, call.timeout_seconds)
    except urllib.error.HTTPError as exc:
        if exc.code >= 500:
            raise RemoteServiceError from exc
        status_code = exc.code
        raw = exc.read().decode("utf-8")
    except (TimeoutError, urllib.error.URLError, OSError) as exc:
        raise RemoteServiceError from exc
    return status_code, _json_object(raw)


def _read_body(
    url: str,
    method: str,
    headers: dict[str, str],
    timeout_seconds: float,
) -> tuple[int, str]:
    request = urllib.request.Request(url, method=method, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        return response.getcode(), response.read().decode("utf-8")


def _json_object(raw: str) -> dict[str, Any]:
    try:
        body = json.loads(raw) if raw else {}
    except json.JSONDecodeError as exc:
        raise RemoteServiceError from exc
    if not isinstance(body, dict):
        raise RemoteServiceError("response was not an object")
    return body

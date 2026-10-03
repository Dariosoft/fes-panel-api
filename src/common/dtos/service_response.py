from dataclasses import dataclass

from common.json_types import JsonBody


@dataclass(frozen=True)
class ServiceResponse:
    status_code: int
    body: JsonBody

from dataclasses import dataclass

from common.json_types import JsonBody


@dataclass(frozen=True)
class CatalogResponse:
    status_code: int
    body: JsonBody

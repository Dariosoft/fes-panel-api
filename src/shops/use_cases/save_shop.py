from common.dtos import ServiceResponse
from common.ports import AccountApiGateway


def save_shop(
    gateway: AccountApiGateway,
    fes_session: str | None,
    body: bytes,
    content_type: str | None,
) -> ServiceResponse:
    return gateway.save_shop(fes_session, body, content_type)

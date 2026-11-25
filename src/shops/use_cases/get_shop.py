from common.dtos import ServiceResponse
from common.ports import AccountApiGateway


def get_shop(gateway: AccountApiGateway, fes_session: str | None) -> ServiceResponse:
    return gateway.get_shop(fes_session)

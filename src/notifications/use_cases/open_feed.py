from typing import IO

from common.ports import NotificationsApiGateway


def open_feed(gateway: NotificationsApiGateway, tenant_id: str) -> IO[bytes]:
    return gateway.open_feed(tenant_id)

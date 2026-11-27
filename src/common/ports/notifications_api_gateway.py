from typing import IO, Protocol


class NotificationsApiGateway(Protocol):
    def open_feed(self, tenant_id: str) -> IO[bytes]:
        """Open the tenant notification feed and return the raw upstream stream."""

import urllib.error
import urllib.request
from typing import IO
from urllib.parse import urlencode

from common.contracts.notifications_api import NOTIFICATIONS_FEED_PATH, TENANT_ID_QUERY_PARAM
from common.errors import NotificationsApiTimeout, NotificationsApiUnavailable
from common.http import is_timeout_error


class NotificationsApiClient:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    def open_feed(self, tenant_id: str) -> IO[bytes]:
        params = urlencode({TENANT_ID_QUERY_PARAM: tenant_id})
        url = f"{self._base_url}{NOTIFICATIONS_FEED_PATH}?{params}"
        request = urllib.request.Request(
            url,
            method="GET",
            headers={"Accept": "text/event-stream"},
        )
        try:
            return urllib.request.urlopen(request)
        except urllib.error.HTTPError as exc:
            exc.close()
            raise NotificationsApiUnavailable from exc
        except (urllib.error.URLError, OSError) as exc:
            if is_timeout_error(exc):
                raise NotificationsApiTimeout from exc
            raise NotificationsApiUnavailable from exc

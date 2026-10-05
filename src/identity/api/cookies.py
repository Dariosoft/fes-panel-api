from django.conf import settings
from django.http import HttpResponse

from common.contracts.account_api import SESSION_COOKIE_NAME
from identity.domain.constants import (
    SESSION_COOKIE_EXPIRES_PAST,
    SESSION_COOKIE_PATH,
    SESSION_COOKIE_SAMESITE,
)


def clear_session_cookie(response: HttpResponse) -> None:
    response.set_cookie(
        SESSION_COOKIE_NAME,
        value="",
        max_age=0,
        expires=SESSION_COOKIE_EXPIRES_PAST,
        path=SESSION_COOKIE_PATH,
        domain=settings.SESSION_COOKIE_DOMAIN,
        secure=bool(getattr(settings, "SESSION_COOKIE_SECURE", False)),
        httponly=True,
        samesite=SESSION_COOKIE_SAMESITE,
    )

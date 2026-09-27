from django.conf import settings
from django.http import HttpResponse

from identity.domain.constants import SESSION_COOKIE_NAME


def clear_session_cookie(response: HttpResponse) -> None:
    response.set_cookie(
        SESSION_COOKIE_NAME,
        value="",
        max_age=0,
        expires="Thu, 01 Jan 1970 00:00:00 GMT",
        path="/",
        domain=settings.SESSION_COOKIE_DOMAIN,
        secure=bool(getattr(settings, "SESSION_COOKIE_SECURE", False)),
        httponly=True,
        samesite="Lax",
    )

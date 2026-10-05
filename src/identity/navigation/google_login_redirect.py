from urllib.parse import urlencode

from common.contracts.account_api import ACCOUNT_LOGIN_GOOGLE_PATH, RETURN_TO_PARAM


def build_google_login_redirect_url(
    account_api_base_url: str,
    panel_public_origin: str,
    return_to: str | None = None,
) -> str:
    base = account_api_base_url.rstrip("/")
    target = f"{panel_public_origin.rstrip('/')}{_safe_path(return_to)}"
    query = urlencode({RETURN_TO_PARAM: target})
    return f"{base}{ACCOUNT_LOGIN_GOOGLE_PATH}?{query}"


def _safe_path(return_to: str | None) -> str:
    if not return_to or not return_to.startswith("/") or return_to.startswith("//"):
        return ""
    return return_to

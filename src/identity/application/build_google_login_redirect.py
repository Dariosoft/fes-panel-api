from urllib.parse import urlencode

from common.contracts.account_api import ACCOUNT_LOGIN_GOOGLE_PATH, RETURN_TO_PARAM


def build_google_login_redirect(account_api_base_url: str, panel_public_origin: str) -> str:
    base = account_api_base_url.rstrip("/")
    query = urlencode({RETURN_TO_PARAM: panel_public_origin})
    return f"{base}{ACCOUNT_LOGIN_GOOGLE_PATH}?{query}"

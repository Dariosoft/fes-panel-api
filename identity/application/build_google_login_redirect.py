from urllib.parse import urlencode


def build_google_login_redirect(account_api_base_url: str, panel_public_origin: str) -> str:
    base = account_api_base_url.rstrip("/")
    query = urlencode({"return_to": panel_public_origin})
    return f"{base}/accounts/login/google?{query}"

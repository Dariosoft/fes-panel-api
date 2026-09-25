"""Typed errors from the account-api HTTP client."""


class AccountClientError(Exception):
    """Base error for account-api client failures."""


class AccountAccessRejected(AccountClientError):
    """Business rejection of Google access or session (4xx auth/business)."""


class AccountServiceUnavailable(AccountClientError):
    """Timeouts, connection failures, or 5xx from account-api."""

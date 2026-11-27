class NotificationsApiUnavailable(Exception):
    """The notifications API could not provide a usable response."""


class NotificationsApiTimeout(NotificationsApiUnavailable):
    """The notifications API did not answer within the configured timeout."""

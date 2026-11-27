class AnalyticsApiUnavailable(Exception):
    """The analytics API could not provide a usable response."""


class AnalyticsApiTimeout(AnalyticsApiUnavailable):
    """The analytics API did not answer within the configured timeout."""

"""Intelligence pipeline exceptions."""


class CaptureError(Exception):
    """Raised when capture cannot proceed (rate limit, paywall, auth required)."""

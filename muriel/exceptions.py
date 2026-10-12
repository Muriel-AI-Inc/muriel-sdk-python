"""Custom exceptions for the Muriel SDK."""


class MurielAPIError(Exception):
    """Base exception for all Muriel API errors."""

    def __init__(self, message: str, status_code: int = None, response: dict = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


class MurielAuthenticationError(MurielAPIError):
    """Raised when API key authentication fails."""

    pass


class MurielValidationError(MurielAPIError):
    """Raised when request validation fails."""

    pass


class MurielNotFoundError(MurielAPIError):
    """Raised when requested resource is not found."""

    pass


class MurielCreditsError(MurielAPIError):
    """HTTP 402: the key's account is out of credits.

    Raised before the call runs -- an agent question or a data call alike --
    so nothing was charged. Agent questions are metered per question; data
    calls cost 1 credit per 1,000 records returned. Email info@murielai.io
    for more credits; the free allowance renews monthly.
    """

    pass


class MurielRateLimitError(MurielAPIError):
    """Raised when rate limit is exceeded."""

    pass


class MurielServerError(MurielAPIError):
    """Raised when server encounters an error."""

    pass


def detail_of(response, default: str) -> str:
    """The server's own explanation from an error response, or `default`."""
    try:
        data = response.json() if response.content else {}
    except ValueError:
        return default
    d = data.get("detail") if isinstance(data, dict) else None
    if isinstance(d, dict):
        d = d.get("message") or d.get("error")
    return str(d) if d else default

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


BUY_CREDITS_EMAIL = "info@murielai.io"
ACCOUNT_URL = "https://murielai.io/account"


class MurielCreditsError(MurielAPIError):
    """HTTP 402: the account is out of Muriel API credits and needs more.

    Raised before the call runs -- an agent question or a data call alike --
    so nothing was charged. The message always says so, plainly, and says how
    to buy more; the server's own wording is kept in `server_message`.

    Attributes:
        balance: the account's credit balance, when the server reported it.
        buy_url: where to buy more credits (an email link).
        account_url: the account page, which shows the balance.
        server_message: the server's explanation, verbatim.
    """

    def __init__(self, message: str = None, status_code: int = 402,
                 response: dict = None):
        detail = (response or {}).get("detail") if isinstance(response, dict) else None
        self.balance = detail.get("balance") if isinstance(detail, dict) else None
        self.server_message = message
        self.buy_url = f"mailto:{BUY_CREDITS_EMAIL}?subject=Muriel%20credits"
        self.account_url = ACCOUNT_URL
        bal = f" (balance: {self.balance})" if self.balance is not None else ""
        text = (
            f"Out of Muriel API credits{bal}. This call was not run and nothing "
            f"was charged. To buy more credits, email {BUY_CREDITS_EMAIL} or use "
            f"'Need more credits' on your account page ({ACCOUNT_URL}). "
            f"Free accounts get 8 credits a month."
        )
        super().__init__(text, status_code=status_code, response=response)


class MurielRateLimitError(MurielAPIError):
    """HTTP 429: more than 60 requests in a minute on one key.

    Attributes:
        retry_after: seconds to wait before retrying, from the response's
            Retry-After header (None if the server did not send one).
    """

    def __init__(self, message: str = "Rate limit exceeded", status_code: int = 429,
                 response: dict = None, retry_after: int = None):
        self.retry_after = retry_after
        super().__init__(message, status_code=status_code, response=response)


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

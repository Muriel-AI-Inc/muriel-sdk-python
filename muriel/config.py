"""Configuration for the Muriel SDK."""

import os
from urllib.parse import urlsplit

# API Configuration
DEFAULT_BASE_URL = "https://api.murielai.io"
DEFAULT_TIMEOUT = 30

# Environment variable names
ENV_API_KEY = "MURIEL_API_KEY"
ENV_BASE_URL = "MURIEL_BASE_URL"


def get_api_key() -> str:
    """Get API key from environment variable."""
    return os.getenv(ENV_API_KEY, "")


def get_base_url() -> str:
    """Get base URL from environment variable or use default."""
    return os.getenv(ENV_BASE_URL, DEFAULT_BASE_URL)


_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def checked_base_url(url: str) -> str:
    """The base URL, refused if it would send the API key in the clear.

    Every request carries the key in a header, so a plain-http base URL hands
    it to anyone on the network path. http is allowed only for a server on
    this machine (local development).
    """
    from .exceptions import MurielAPIError

    url = (url or "").strip().rstrip("/")
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    if parts.scheme == "https" and host:
        return url
    if parts.scheme == "http" and host in _LOCAL_HOSTS:
        return url
    raise MurielAPIError(
        f"Refusing base URL {url!r}: use https:// (plain http is allowed only for "
        "localhost), so your API key is never sent unencrypted.")

"""Core client for the Muriel API."""

from typing import Any, Dict, Optional
import requests

from .config import DEFAULT_BASE_URL, DEFAULT_TIMEOUT, checked_base_url, get_api_key, get_base_url
from .exceptions import (
    MurielAPIError,
    MurielAuthenticationError,
    MurielValidationError,
    MurielNotFoundError,
    MurielRateLimitError,
    MurielServerError,
    MurielCreditsError,
    detail_of,
)


class MurielClient:
    """Base client for making requests to the Muriel API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """
        Initialize the Muriel API client.

        Args:
            api_key: Your Muriel API key. If not provided, will look for MURIEL_API_KEY env var.
            base_url: Base URL for the API (default: MURIEL_BASE_URL, else https://api.murielai.io)
            timeout: Request timeout in seconds (default: 30)
        """
        self.api_key = api_key or get_api_key()
        if not self.api_key:
            raise MurielAuthenticationError(
                "API key is required. Pass it as api_key parameter or set MURIEL_API_KEY environment variable."
            )

        self.base_url = checked_base_url(base_url or get_base_url())
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"X-API-Key": self.api_key})

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            json: JSON body data

        Returns:
            Response data as dictionary

        Raises:
            MurielAPIError: For various API errors
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                timeout=self.timeout,
                # Never follow a redirect: requests strips Authorization on a
                # cross-host redirect but NOT a custom X-API-Key header, so a
                # redirect would hand the key to whatever host it points at.
                allow_redirects=False,
            )
            if 300 <= response.status_code < 400:
                raise MurielAPIError(
                    f"Unexpected redirect ({response.status_code}) to "
                    f"{response.headers.get('Location', '?')}; not followed, so your API "
                    "key was not sent there. Check MURIEL_BASE_URL.",
                    status_code=response.status_code,
                )

            # Handle different status codes
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 201:
                return response.json()
            elif response.status_code == 401:
                raise MurielAuthenticationError(
                    "Invalid API key",
                    status_code=response.status_code,
                    response=response.json() if response.content else None,
                )
            elif response.status_code == 400:
                error_data = response.json() if response.content else {}
                raise MurielValidationError(
                    error_data.get("detail", "Validation error"),
                    status_code=response.status_code,
                    response=error_data,
                )
            elif response.status_code == 402:
                raise MurielCreditsError(
                    detail_of(response, ""),
                    status_code=402,
                    response=response.json() if response.content else None,
                )
            elif response.status_code == 404:
                raise MurielNotFoundError(
                    detail_of(response, "Resource not found"),
                    status_code=response.status_code,
                    response=response.json() if response.content else None,
                )
            elif response.status_code == 429:
                try:
                    retry_after = int(response.headers.get("Retry-After"))
                except (TypeError, ValueError):
                    retry_after = None
                raise MurielRateLimitError(
                    detail_of(response, "Rate limit exceeded"),
                    status_code=response.status_code,
                    response=response.json() if response.content else None,
                    retry_after=retry_after,
                )
            elif response.status_code >= 500:
                raise MurielServerError(
                    detail_of(response, "Server error"),
                    status_code=response.status_code,
                    response=response.json() if response.content else None,
                )
            else:
                response.raise_for_status()
                return response.json()

        except requests.exceptions.Timeout:
            raise MurielAPIError(f"Request timed out after {self.timeout} seconds")
        except requests.exceptions.ConnectionError:
            raise MurielAPIError(f"Failed to connect to {self.base_url}")
        except requests.exceptions.RequestException as e:
            if not isinstance(e, MurielAPIError):
                raise MurielAPIError(f"Request failed: {str(e)}")
            raise

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a GET request."""
        return self._make_request("GET", endpoint, params=params)

    def post(self, endpoint: str, json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a POST request."""
        return self._make_request("POST", endpoint, json=json)

    def close(self):
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

"""Water system list endpoints."""

from typing import Any, Dict, Optional

from ..client import MurielClient


def get_systems(
    state: str,
    api_key: Optional[str] = None,
    limit: int = 100,
    system_princ: Optional[str] = None,
    system_statu: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get public water systems for a state.

    Maps to GET /api/v1/systems/{state}.
    Optional system_princ and system_statu are passed as query parameters when provided.
    """
    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url

    params: Dict[str, Any] = {"limit": limit}
    if system_princ is not None:
        params["system_princ"] = system_princ
    if system_statu is not None:
        params["system_statu"] = system_statu

    with MurielClient(**client_kwargs) as client:
        endpoint = f"/api/v1/systems/{state.upper()}"
        return client.get(endpoint, params=params)

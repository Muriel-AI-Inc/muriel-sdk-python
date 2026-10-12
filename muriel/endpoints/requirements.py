"""Sampling requirements endpoints."""

from typing import Any, Dict, Optional

from ..client import MurielClient


def get_requirements(
    pwsid: Optional[str] = None,
    state: Optional[str] = None,
    api_key: Optional[str] = None,
    limit: int = 100,
    system_princ: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get water quality sampling requirements by system or state.

    - GET /api/v1/requirements/system/{pwsid}
    - GET /api/v1/requirements/state/{state}
    """
    if not pwsid and not state:
        raise ValueError("Must provide either pwsid or state")

    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url

    with MurielClient(**client_kwargs) as client:
        if pwsid:
            endpoint = f"/api/v1/requirements/system/{pwsid}"
            params: Dict[str, Any] = {}
        else:
            endpoint = f"/api/v1/requirements/state/{state.upper()}"
            params = {"limit": limit}
            if system_princ is not None:
                params["system_princ"] = system_princ

        return client.get(endpoint, params=params or None)

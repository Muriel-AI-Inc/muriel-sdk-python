"""Compliance and violations endpoints."""

from typing import Any, Dict, Optional

from ..client import MurielClient


def get_violations(
    pwsid: Optional[str] = None,
    state: Optional[str] = None,
    api_key: Optional[str] = None,
    limit: int = 100,
    violation_status: Optional[str] = None,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get compliance violations by system or state.

    - GET /api/v1/violations/system/{pwsid}
    - GET /api/v1/violations/state/{state}
    """
    if not pwsid and not state:
        raise ValueError("Must provide either pwsid or state")

    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url

    params: Dict[str, Any] = {"limit": limit}
    if violation_status is not None:
        params["violation_status"] = violation_status
    if date_start is not None:
        params["date_start"] = date_start
    if date_end is not None:
        params["date_end"] = date_end

    with MurielClient(**client_kwargs) as client:
        if pwsid:
            endpoint = f"/api/v1/violations/system/{pwsid}"
        else:
            endpoint = f"/api/v1/violations/state/{state.upper()}"

        return client.get(endpoint, params=params)

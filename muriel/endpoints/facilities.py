"""Facilities and geocoding endpoints."""

from typing import Dict, Any, Optional

from ..client import MurielClient


def get_state_facilities(
    state: str,
    api_key: Optional[str] = None,
    limit: int = 100,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get facilities with geocoding data for a specific state.

    Args:
        state: State abbreviation (e.g., 'IL', 'CA')
        api_key: Your Muriel API key
        limit: Maximum number of facilities to return (default: 100)
        base_url: Override base API URL

    Returns:
        Dictionary containing facility data with geocoding

    Example:
        >>> facilities = get_state_facilities(
        ...     state='IL',
        ...     api_key='YOUR_API_KEY',
        ...     limit=100
        ... )
        >>> print(f"Found {facilities['facility_count']} facilities")
        >>> for facility in facilities['facilities']:
        ...     if facility.get('geocoding'):
        ...         print(f"{facility['pwsid']}: {facility['geocoding']['address_formatted']}")
    """
    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url

    with MurielClient(**client_kwargs) as client:
        endpoint = f"/api/v1/geocoding/facilities/state/{state.upper()}"
        params = {"limit": limit}
        return client.get(endpoint, params=params)


def get_facility_geocoding(
    pwsid: str,
    facility_id: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get geocoding data for a specific facility.

    Args:
        pwsid: Public Water System ID (e.g., 'IL0316000')
        facility_id: State-assigned facility identifier
        api_key: Your Muriel API key
        base_url: Override base API URL

    Returns:
        Dictionary containing facility geocoding data

    Example:
        >>> facility = get_facility_geocoding(
        ...     pwsid='IL0316000',
        ...     facility_id='FAC001',
        ...     api_key='YOUR_API_KEY'
        ... )
        >>> if facility['found']:
        ...     geo = facility['geocoding']
        ...     print(f"Location: {geo['latitude']}, {geo['longitude']}")
        ...     print(f"Address: {geo['address_formatted']}")
    """
    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url

    with MurielClient(**client_kwargs) as client:
        endpoint = f"/api/v1/geocoding/facility/{pwsid}/{facility_id}"
        return client.get(endpoint)

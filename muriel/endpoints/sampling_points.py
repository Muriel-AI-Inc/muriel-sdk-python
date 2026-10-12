"""Sampling points and geocoding endpoints."""

from typing import Dict, Any, Optional

from ..client import MurielClient


def get_state_sampling_points(
    state: str,
    api_key: Optional[str] = None,
    limit: int = 100,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get sampling points with geocoding data for a specific state.

    Args:
        state: State abbreviation (e.g., 'IL', 'CA')
        api_key: Your Muriel API key
        limit: Maximum number of sampling points to return (default: 100)
        base_url: Override base API URL

    Returns:
        Dictionary containing sampling point data with geocoding

    Example:
        >>> sampling_points = get_state_sampling_points(
        ...     state='IL',
        ...     api_key='YOUR_API_KEY',
        ...     limit=100
        ... )
        >>> print(f"Found {sampling_points['sampling_point_count']} sampling points")
        >>> for sp in sampling_points['sampling_points']:
        ...     if sp.get('geocoding'):
        ...         print(f"{sp['sample_point']}: {sp['geocoding']['address_formatted']}")
    """
    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url

    with MurielClient(**client_kwargs) as client:
        endpoint = f"/api/v1/geocoding/sampling_points/state/{state.upper()}"
        params = {"limit": limit}
        return client.get(endpoint, params=params)


def get_sampling_point_geocoding(
    pwsid: str,
    sample_point: str,
    facility_id: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get geocoding data for a specific sampling point.

    Args:
        pwsid: Public Water System ID (e.g., 'IL0316000')
        sample_point: Sampling point identifier
        facility_id: Optional state-assigned facility identifier for disambiguation
        api_key: Your Muriel API key
        base_url: Override base API URL

    Returns:
        Dictionary containing sampling point geocoding data

    Example:
        >>> sampling_point = get_sampling_point_geocoding(
        ...     pwsid='IL0316000',
        ...     sample_point='LP1A024',
        ...     api_key='YOUR_API_KEY'
        ... )
        >>> if sampling_point['found']:
        ...     geo = sampling_point['geocoding']
        ...     print(f"Location: {geo['latitude']}, {geo['longitude']}")
    """
    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url

    with MurielClient(**client_kwargs) as client:
        if facility_id:
            endpoint = f"/api/v1/geocoding/sampling_point/{pwsid}/{facility_id}/{sample_point}"
        else:
            endpoint = f"/api/v1/geocoding/sampling_point/{pwsid}/{sample_point}"
        return client.get(endpoint)

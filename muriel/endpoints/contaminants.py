"""Convenience functions for common contaminant queries."""

from typing import List, Optional, Dict, Any

from ..client import MurielClient


def get_latest(
    limit: int = 10,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Get the most recent water quality test results globally.

    Args:
        limit: Number of results to return (default: 10, max: 1000)
        api_key: Your Muriel API key
        base_url: Override base API URL

    Returns:
        List of most recent water quality records

    Example:
        >>> records = get_latest(limit=50, api_key='YOUR_API_KEY')
    """
    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url

    with MurielClient(**client_kwargs) as client:
        response = client.get("/api/v1/records/latest", params={"limit": limit})
        return response.get("records", [])


def get_lead(
    limit: int = 100,
    detections_only: bool = False,
    min_concentration: Optional[float] = None,
    geocoded_only: bool = False,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    era: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Get lead test results globally.

    Args:
        limit: Number of results to return (default: 100, max: 1000)
        detections_only: Only return detected results (value > 0)
        min_concentration: Minimum concentration (e.g., 0.015 for EPA action level)
        geocoded_only: Only return records with coordinates
        api_key: Your Muriel API key
        base_url: Override base API URL
        era: "recent" (default: the window states currently publish) or "all"
             (include the historical archive)

    Returns:
        List of lead test records

    Example:
        >>> # Get lead above EPA action level (15 ppb = 0.015 mg/L)
        >>> records = get_lead(min_concentration=0.015, api_key='YOUR_API_KEY')
    """
    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url

    with MurielClient(**client_kwargs) as client:
        params = {"limit": limit}
        if detections_only:
            params["detections_only"] = True
        if min_concentration is not None:
            params["min_concentration"] = min_concentration
        if geocoded_only:
            params["geocoded_only"] = True

        if era:
            params["era"] = era
        response = client.get("/api/v1/records/lead", params=params)
        return response.get("records", [])


def get_pfas(
    limit: int = 100,
    detections_only: bool = False,
    min_concentration: Optional[float] = None,
    result_analyte_name: Optional[str] = None,
    geocoded_only: bool = False,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    era: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Get PFAS (forever chemicals) test results globally.

    Args:
        limit: Number of results to return (default: 100, max: 1000)
        detections_only: Only return detected results (value > 0)
        min_concentration: Minimum concentration (e.g., 0.004 for EPA advisory)
        result_analyte_name: Filter by specific PFAS (e.g., 'PERFLUOROCTANOIC ACID (PFOA)')
        geocoded_only: Only return records with coordinates
        api_key: Your Muriel API key
        base_url: Override base API URL
        era: "recent" (default: the window states currently publish) or "all"
             (include the historical archive)

    Returns:
        List of PFAS test records

    Example:
        >>> # Get PFAS above EPA health advisory (4 ppt = 0.004 ug/L)
        >>> records = get_pfas(min_concentration=0.004, api_key='YOUR_API_KEY')

        >>> # Get only PFOA tests
        >>> pfoa = get_pfas(result_analyte_name='PERFLUOROCTANOIC ACID (PFOA)', api_key='YOUR_API_KEY')
    """
    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url

    with MurielClient(**client_kwargs) as client:
        params = {"limit": limit}
        if detections_only:
            params["detections_only"] = True
        if min_concentration is not None:
            params["min_concentration"] = min_concentration
        if result_analyte_name:
            params["result_analyte_name"] = result_analyte_name
        if geocoded_only:
            params["geocoded_only"] = True

        if era:
            params["era"] = era
        response = client.get("/api/v1/records/pfas", params=params)
        return response.get("records", [])


def get_coliform(
    limit: int = 100,
    presence_indicator: Optional[str] = None,
    geocoded_only: bool = False,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    era: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Get coliform (TCR) and E. coli test results globally.

    Args:
        limit: Number of results to return (default: 100, max: 1000)
        presence_indicator: Filter by presence ('P' = detected, 'A' = not detected)
        geocoded_only: Only return records with coordinates
        api_key: Your Muriel API key
        base_url: Override base API URL
        era: "recent" (default: the window states currently publish) or "all"
             (include the historical archive)

    Returns:
        List of coliform and E. coli test records

    Example:
        >>> # Get all coliform tests
        >>> records = get_coliform(limit=200, api_key='YOUR_API_KEY')

        >>> # Get only positive coliform detections
        >>> positive = get_coliform(presence_indicator='P', api_key='YOUR_API_KEY')
    """
    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url

    with MurielClient(**client_kwargs) as client:
        params = {"limit": limit}
        if presence_indicator:
            params["presence_indicator"] = presence_indicator
        if geocoded_only:
            params["geocoded_only"] = True

        if era:
            params["era"] = era
        response = client.get("/api/v1/records/coliform", params=params)
        return response.get("records", [])


def get_nitrate(
    limit: int = 100,
    detections_only: bool = False,
    min_concentration: Optional[float] = None,
    geocoded_only: bool = False,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    era: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Get nitrate and nitrate-nitrite test results globally.

    Args:
        limit: Number of results to return (default: 100, max: 1000)
        detections_only: Only return detected results (value > 0)
        min_concentration: Minimum concentration (e.g., 10 for EPA MCL)
        geocoded_only: Only return records with coordinates
        api_key: Your Muriel API key
        base_url: Override base API URL
        era: "recent" (default: the window states currently publish) or "all"
             (include the historical archive)

    Returns:
        List of nitrate test records

    Example:
        >>> # Get nitrate above EPA MCL (10 mg/L)
        >>> records = get_nitrate(min_concentration=10, api_key='YOUR_API_KEY')
    """
    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url

    with MurielClient(**client_kwargs) as client:
        params = {"limit": limit}
        if detections_only:
            params["detections_only"] = True
        if min_concentration is not None:
            params["min_concentration"] = min_concentration
        if geocoded_only:
            params["geocoded_only"] = True

        if era:
            params["era"] = era
        response = client.get("/api/v1/records/nitrate", params=params)
        return response.get("records", [])


def get_dbps(
    limit: int = 100,
    detections_only: bool = False,
    min_concentration: Optional[float] = None,
    result_analyte_name: Optional[str] = None,
    geocoded_only: bool = False,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    era: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Get disinfection by-products (DBPs) test results globally.

    Args:
        limit: Number of results to return (default: 100, max: 1000)
        detections_only: Only return detected results (value > 0)
        min_concentration: Minimum concentration
        result_analyte_name: Filter by specific DBP (e.g., 'TTHM', 'HAA5')
        geocoded_only: Only return records with coordinates
        api_key: Your Muriel API key
        base_url: Override base API URL
        era: "recent" (default: the window states currently publish) or "all"
             (include the historical archive)

    Returns:
        List of DBP test records

    Example:
        >>> # Get all DBP tests
        >>> records = get_dbps(limit=200, api_key='YOUR_API_KEY')

        >>> # Get only TTHM tests
        >>> tthm = get_dbps(result_analyte_name='TTHM', api_key='YOUR_API_KEY')
    """
    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url

    with MurielClient(**client_kwargs) as client:
        params = {"limit": limit}
        if detections_only:
            params["detections_only"] = True
        if min_concentration is not None:
            params["min_concentration"] = min_concentration
        if result_analyte_name:
            params["result_analyte_name"] = result_analyte_name
        if geocoded_only:
            params["geocoded_only"] = True

        if era:
            params["era"] = era
        response = client.get("/api/v1/records/dbps", params=params)
        return response.get("records", [])


def get_arsenic(
    limit: int = 100,
    detections_only: bool = False,
    min_concentration: Optional[float] = None,
    geocoded_only: bool = False,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    era: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Get arsenic test results globally.

    Args:
        limit: Number of results to return (default: 100, max: 1000)
        detections_only: Only return detected results (value > 0)
        min_concentration: Minimum concentration (e.g., 0.010 for EPA MCL)
        geocoded_only: Only return records with coordinates
        api_key: Your Muriel API key
        base_url: Override base API URL
        era: "recent" (default: the window states currently publish) or "all"
             (include the historical archive)

    Returns:
        List of arsenic test records

    Example:
        >>> # Get arsenic above EPA MCL (10 ppb = 0.010 mg/L)
        >>> records = get_arsenic(min_concentration=0.010, api_key='YOUR_API_KEY')
    """
    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url

    with MurielClient(**client_kwargs) as client:
        params = {"limit": limit}
        if detections_only:
            params["detections_only"] = True
        if min_concentration is not None:
            params["min_concentration"] = min_concentration
        if geocoded_only:
            params["geocoded_only"] = True

        if era:
            params["era"] = era
        response = client.get("/api/v1/records/arsenic", params=params)
        return response.get("records", [])


def get_manganese(
    limit: int = 100,
    detections_only: bool = False,
    min_concentration: Optional[float] = None,
    geocoded_only: bool = False,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    era: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Get manganese test results globally.

    Args:
        limit: Number of results to return (default: 100, max: 1000)
        detections_only: Only return detected results (value > 0)
        min_concentration: Minimum concentration (e.g., 0.05 for EPA secondary MCL)
        geocoded_only: Only return records with coordinates
        api_key: Your Muriel API key
        base_url: Override base API URL
        era: "recent" (default: the window states currently publish) or "all"
             (include the historical archive)

    Returns:
        List of manganese test records

    Example:
        >>> # Get manganese above EPA secondary MCL (0.05 mg/L)
        >>> records = get_manganese(min_concentration=0.05, api_key='YOUR_API_KEY')
    """
    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url

    with MurielClient(**client_kwargs) as client:
        params = {"limit": limit}
        if detections_only:
            params["detections_only"] = True
        if min_concentration is not None:
            params["min_concentration"] = min_concentration
        if geocoded_only:
            params["geocoded_only"] = True

        if era:
            params["era"] = era
        response = client.get("/api/v1/records/manganese", params=params)
        return response.get("records", [])


def get_vocs(
    limit: int = 100,
    detections_only: bool = False,
    min_concentration: Optional[float] = None,
    result_analyte_name: Optional[str] = None,
    geocoded_only: bool = False,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    era: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Get volatile organic compounds (VOCs) test results globally.

    Args:
        limit: Number of results to return (default: 100, max: 1000)
        detections_only: Only return detected results (value > 0)
        min_concentration: Minimum concentration
        result_analyte_name: Filter by specific VOC (e.g., 'BENZENE', 'TOLUENE')
        geocoded_only: Only return records with coordinates
        api_key: Your Muriel API key
        base_url: Override base API URL
        era: "recent" (default: the window states currently publish) or "all"
             (include the historical archive)

    Returns:
        List of VOC test records

    Example:
        >>> # Get all VOC tests
        >>> records = get_vocs(limit=200, api_key='YOUR_API_KEY')

        >>> # Get only benzene tests
        >>> benzene = get_vocs(result_analyte_name='BENZENE', api_key='YOUR_API_KEY')
    """
    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url

    with MurielClient(**client_kwargs) as client:
        params = {"limit": limit}
        if detections_only:
            params["detections_only"] = True
        if min_concentration is not None:
            params["min_concentration"] = min_concentration
        if result_analyte_name:
            params["result_analyte_name"] = result_analyte_name
        if geocoded_only:
            params["geocoded_only"] = True

        if era:
            params["era"] = era
        response = client.get("/api/v1/records/vocs", params=params)
        return response.get("records", [])

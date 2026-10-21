"""Water quality sample results endpoints."""

import warnings
from typing import List, Optional, Dict, Any

from ..client import MurielClient
from ..exceptions import MurielValidationError
from ..utils import (
    build_sort_param,
    extract_records,
    resolve_analyte,
    resolve_limit,
)

# The API returns at most this many records per request; larger requests page.
PAGE_SIZE = 1000
# Distinguishes limit=None ("everything") from limit left out (the default).
_DEFAULT = object()


def _append_filter_params(
    params: Dict[str, Any],
    *,
    analyte_name: Optional[str],
    detections_only: bool,
    geocoded_only: bool,
    min_concentration: Optional[float],
    exclude_censored: bool,
    presence_indicator: Optional[str],
    offset: int,
) -> None:
    if analyte_name:
        params["result_analyte_name"] = analyte_name
    if detections_only:
        params["detections_only"] = True
    if geocoded_only:
        params["geocoded_only"] = True
    if min_concentration is not None:
        params["min_concentration"] = min_concentration
    if exclude_censored:
        params["exclude_censored"] = True
    if presence_indicator is not None:
        params["presence_indicator"] = presence_indicator
    if offset:
        params["offset"] = offset


def get_results(
    pwsid: Optional[str] = None,
    address: Optional[str] = None,
    state: Optional[str] = None,
    analyte: Optional[str] = None,
    result_analyte_name: Optional[str] = None,
    analyte_group: Optional[str] = None,
    api_key: Optional[str] = None,
    num: Optional[int] = None,
    limit: Any = _DEFAULT,
    latest: bool = True,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    radius_miles: float = 10.0,
    geocoded_only: bool = False,
    detections_only: bool = False,
    cas_number: Optional[str] = None,
    min_concentration: Optional[float] = None,
    exclude_censored: bool = False,
    presence_indicator: Optional[str] = None,
    offset: int = 0,
    base_url: Optional[str] = None,
    era: Optional[str] = None,
    **extra_params: Any,
) -> List[Dict[str, Any]]:
    """
    Query water quality sample results.

    Accepts ``analyte`` or ``result_analyte_name`` (synonyms) and ``num`` or
    ``limit`` for the number of records. Left out, ``limit`` is 10.
    ``limit=None`` returns every matching record, and a limit over 1,000 is
    fetched in pages of 1,000 -- the SDK pages for you. A single system
    (``pwsid``) pages through its whole record; a state, analyte group or
    address query stops at the API's 10,000-record offset limit with a warning
    (narrow it with dates or an analyte). Large pulls are billed like any other:
    1 credit per 1,000 records.

    ``era``: ``"all"`` includes the historical archive, ``"recent"`` is the
    window states currently publish. Left unset, the server decides: history
    for a system, state or address; the current window for an analyte group.
    """
    if cas_number:
        raise MurielValidationError(
            "cas_number filtering is not available: results do not carry CAS "
            "numbers. Filter by analyte name (analyte=...) instead.")
    if era is not None and era not in ("all", "recent"):
        raise MurielValidationError('era must be "all" or "recent".')
    # limit=None means every record; left out, the default (num, else 10).
    want: Optional[int] = (resolve_limit(num=num, limit=None) if limit is _DEFAULT
                           else None if limit is None else int(limit))
    if want is not None and want < 1:
        raise MurielValidationError("limit must be at least 1, or None for every record.")
    analyte_name = resolve_analyte(analyte, result_analyte_name)
    sort_value = build_sort_param(latest)

    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url

    with MurielClient(**client_kwargs) as client:
        params: Dict[str, Any] = {}
        if sort_value:
            params["sort"] = sort_value

        _append_filter_params(
            params,
            analyte_name=analyte_name,
            detections_only=detections_only,
            geocoded_only=geocoded_only,
            min_concentration=min_concentration,
            exclude_censored=exclude_censored,
            presence_indicator=presence_indicator,
            offset=offset,
        )
        params.update(extra_params)

        if era:
            params["era"] = era

        # The server filters by analyte group on every route, so a page is a
        # full page (filtering client-side used to return short, unpageable
        # pages for a state + group query).
        if address:
            endpoint = "/api/v1/records/address"
            params["address"] = address
            params["radius_miles"] = radius_miles
            if analyte_group:
                params["analyte_group"] = analyte_group
        elif pwsid:
            endpoint = f"/api/v1/records/system/{pwsid.strip().upper()}"
            if analyte_group:
                params["analyte_group"] = analyte_group
        elif state:
            endpoint = f"/api/v1/records/state/{state.strip().upper()}"
            if analyte_group:
                params["analyte_group"] = analyte_group
        elif analyte_group:
            endpoint = f"/api/v1/records/group/{analyte_group}"
        else:
            raise MurielValidationError(
                "Give at least one of: pwsid, address, state, or analyte_group."
            )

        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        if want is not None and want <= PAGE_SIZE:
            response = client.get(endpoint, params={**params, "limit": want})
            return extract_records(response)
        return _all_pages(client, endpoint, params, want, offset)


def _all_pages(client: MurielClient, endpoint: str, params: Dict[str, Any],
               want: Optional[int], offset: int) -> List[Dict[str, Any]]:
    """Up to `want` records (None: all), PAGE_SIZE at a time, from `offset`."""
    out: List[Dict[str, Any]] = []
    at = offset
    while want is None or len(out) < want:
        size = PAGE_SIZE if want is None else min(PAGE_SIZE, want - len(out))
        response = client.get(endpoint, params={**params, "limit": size, "offset": at})
        page = extract_records(response)
        out.extend(page)
        at += len(page)
        pag = response.get("pagination") or {} if isinstance(response, dict) else {}
        if pag.get("offset_limit_reached"):
            warnings.warn(
                f"Stopped at {len(out):,} records: the API pages state, analyte-group and "
                f"address queries up to an offset of {pag.get('max_offset', 10_000):,}. "
                "Narrow the query (start_date/end_date, analyte) or ask for one system "
                "with pwsid=, which pages through its whole record.", stacklevel=3)
            break
        if not page or not pag.get("has_more", len(page) >= size):
            break
    return out

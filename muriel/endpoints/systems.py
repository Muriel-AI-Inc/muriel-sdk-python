"""Water system list endpoints."""

from typing import Any, Dict, Optional

from ..client import MurielClient

# The most the server returns in one call; limit=None pages at this size.
MAX_PAGE = 20000


def get_systems(
    state: str,
    api_key: Optional[str] = None,
    limit: Optional[int] = 100,
    offset: int = 0,
    system_princ: Optional[str] = None,
    system_statu: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get public water systems for a state, ordered by PWSID.

    Maps to GET /api/v1/systems/{state}.

    limit: how many systems to return (up to 20,000 per call). Pass None for
        every system in the state; the SDK pages through them for you.
    offset: how many systems to skip, for paging by hand.

    The response has ``records`` (one dict per system), ``system_count`` (how
    many came back), ``total_systems`` (how many the state has) and
    ``has_more`` (whether another page follows).

    system_princ and system_statu are sent as query parameters when given;
    the current API does not filter on them.
    """
    client_kwargs: Dict[str, Any] = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url

    params: Dict[str, Any] = {}
    if system_princ is not None:
        params["system_princ"] = system_princ
    if system_statu is not None:
        params["system_statu"] = system_statu

    endpoint = f"/api/v1/systems/{state.strip().upper()}"
    with MurielClient(**client_kwargs) as client:
        if limit is not None:
            return client.get(endpoint, params={**params, "limit": limit, "offset": offset})

        # Every system: page until the server says there are no more.
        records, pwsids, resp = [], [], {}
        at = offset
        while True:
            resp = client.get(endpoint, params={**params, "limit": MAX_PAGE, "offset": at})
            page = resp.get("records") or []
            records.extend(page)
            pwsids.extend(resp.get("systems") or [r.get("pwsid") for r in page])
            at += len(page)
            if not page or not resp.get("has_more", len(page) >= MAX_PAGE):
                break
        out = dict(resp)
        out.update({"records": records, "systems": pwsids, "system_count": len(records),
                    "limit": None, "offset": offset, "has_more": False})
        out.setdefault("total_systems", offset + len(records))
        return out

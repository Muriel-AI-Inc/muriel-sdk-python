"""Fetching more than one page: shared by get_results and the contaminant feeds.

The API returns at most PAGE_SIZE records per request. Two kinds of route:

* The nationwide feeds (/records/lead and the rest) and /records/group answer
  with ``pagination.next_cursor``; the next page passes it back as ``cursor``.
  No depth limit.
* System, state and address routes page by ``offset``. One system pages
  through its whole record; a state or area stops at the API's offset limit,
  and this says so.

A rate-limited page (60 requests a minute per key) is retried after a pause
rather than losing the pages already fetched.
"""
import time
import warnings
from typing import Any, Dict, List, Optional

from .client import MurielClient
from .exceptions import MurielRateLimitError, MurielValidationError
from .utils import extract_records

PAGE_SIZE = 1000
RATE_LIMIT_WAIT = 20      # seconds; what the API's Retry-After says
RATE_LIMIT_TRIES = 6


def check_limit(limit: Optional[int]) -> Optional[int]:
    """None means every record; otherwise a positive int."""
    if limit is None:
        return None
    limit = int(limit)
    if limit < 1:
        raise MurielValidationError("limit must be at least 1, or None for every record.")
    return limit


def _get(client: MurielClient, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    for attempt in range(RATE_LIMIT_TRIES):
        try:
            return client.get(endpoint, params=params)
        except MurielRateLimitError as err:
            if attempt == RATE_LIMIT_TRIES - 1:
                raise
            time.sleep(RATE_LIMIT_WAIT if err.retry_after is None
                       else min(err.retry_after, RATE_LIMIT_WAIT * 3))
    raise AssertionError("unreachable")


def fetch_pages(client: MurielClient, endpoint: str, params: Dict[str, Any],
                want: Optional[int], offset: int = 0) -> List[Dict[str, Any]]:
    """Up to `want` records (None: all), PAGE_SIZE at a time."""
    out: List[Dict[str, Any]] = []
    at, cursor = offset, None
    while want is None or len(out) < want:
        size = PAGE_SIZE if want is None else min(PAGE_SIZE, want - len(out))
        q = {**params, "limit": size}
        if cursor:
            q["cursor"] = cursor
        else:
            q["offset"] = at
        response = _get(client, endpoint, q)
        page = extract_records(response)
        out.extend(page)
        at += len(page)
        pag = (response.get("pagination") or {}) if isinstance(response, dict) else {}
        if pag.get("offset_limit_reached"):
            warnings.warn(
                f"Stopped at {len(out):,} records: the API pages state, analyte-group and "
                f"address queries up to an offset of {pag.get('max_offset', 10_000):,}. "
                "Narrow the query (start_date/end_date, analyte) or ask for one system "
                "with pwsid=, which pages through its whole record.", stacklevel=3)
            break
        if not page or not pag.get("has_more"):
            break
        cursor = pag.get("next_cursor")
    return out[:want] if want is not None else out

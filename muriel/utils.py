"""Shared helpers for endpoint modules."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional


def extract_records(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Pull record list from common API response shapes."""
    if "records" in response:
        return response["records"]
    if "results" in response:
        return response["results"]
    return response if isinstance(response, list) else []


def resolve_analyte(
    analyte: Optional[str] = None,
    result_analyte_name: Optional[str] = None,
) -> Optional[str]:
    """Accept either analyte or result_analyte_name (docs use both)."""
    return analyte or result_analyte_name


def resolve_limit(num: Optional[int] = None, limit: Optional[int] = None) -> int:
    """Accept num or limit for result count."""
    if limit is not None:
        return limit
    if num is not None:
        return num
    return 10


def build_sort_param(latest: bool) -> Optional[str]:
    return "recent" if latest else None


def apply_client_filters(
    records: List[Dict[str, Any]],
    *,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    cas_number: Optional[str] = None,
    analyte_group: Optional[str] = None,
    state: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Filters not supported server-side on all endpoints."""
    filtered = records

    if state:
        state_upper = state.upper()
        filtered = [
            r
            for r in filtered
            if (r.get("state") or "").upper() == state_upper
        ]

    if analyte_group:
        group_lower = analyte_group.lower()
        filtered = [
            r
            for r in filtered
            if (r.get("analyte_group") or "").lower() == group_lower
        ]

    if cas_number:
        cas_normalized = cas_number.strip().lower()
        filtered = [
            r
            for r in filtered
            if (r.get("result_analyte_cas_number") or "").strip().lower()
            == cas_normalized
        ]

    if start_date or end_date:
        start = _parse_date(start_date) if start_date else None
        end = _parse_date(end_date) if end_date else None
        date_filtered: List[Dict[str, Any]] = []
        for record in filtered:
            record_date = _parse_date(record.get("sample_collection_date"))
            if record_date is None:
                continue
            if start and record_date < start:
                continue
            if end and record_date > end:
                continue
            date_filtered.append(record)
        filtered = date_filtered

    return filtered


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text[:19], fmt)
        except ValueError:
            continue
    return None

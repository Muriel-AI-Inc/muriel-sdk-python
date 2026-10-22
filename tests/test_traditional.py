"""The traditional functions: the request each one sends, and its errors.

No network: requests.Session.request is replaced with a stub that records the
call and returns a canned response.

    python -m pytest tests/test_traditional.py
    python tests/test_traditional.py          # without pytest
"""
import os

import requests

import muriel
from muriel import (MurielCreditsError, MurielServerError, MurielValidationError,
                    SystemsClient, get_lead, get_results)

KEY = "muriel_live_" + "t" * 32
SENT = []


class _Resp:
    def __init__(self, status=200, body=None):
        self.status_code = status
        self._body = {"records": []} if body is None else body
        self.content = b"x"
        self.headers = {}

    def json(self):
        return self._body

    def raise_for_status(self):
        raise requests.HTTPError(str(self.status_code))


NEXT = {"resp": _Resp()}


def _request(self, method, url, params=None, json=None, timeout=None, **kw):
    SENT.append({"method": method, "url": url, "params": dict(params or {}),
                 "key": self.headers.get("X-API-Key")})
    return NEXT["resp"]


requests.Session.request = _request


def _last():
    return SENT[-1]


def test_system_results_go_to_the_system_route():
    NEXT["resp"] = _Resp(body={"records": [{"pwsid": "IL0316000", "era": "historical"}]})
    rows = get_results(pwsid="il0316000", analyte="Lead", limit=10, api_key=KEY)
    s = _last()
    assert s["url"].endswith("/api/v1/records/system/IL0316000")
    assert s["params"]["limit"] == 10 and "Lead" in s["params"].values()
    assert s["key"] == KEY and rows[0]["era"] == "historical"


def test_state_and_group_are_filtered_on_the_server():
    NEXT["resp"] = _Resp()
    get_results(state="il", analyte_group="pfas", api_key=KEY)
    s = _last()
    assert s["url"].endswith("/api/v1/records/state/IL")
    assert s["params"]["analyte_group"] == "pfas"


def test_address_sends_radius():
    get_results(address="233 S Wacker Dr, Chicago, IL", radius_miles=5, api_key=KEY)
    s = _last()
    assert s["url"].endswith("/api/v1/records/address")
    assert s["params"]["radius_miles"] == 5


def test_era_is_passed_and_checked():
    get_lead(limit=5, era="all", api_key=KEY)
    assert _last()["url"].endswith("/api/v1/records/lead") and _last()["params"]["era"] == "all"
    try:
        get_results(pwsid="IL0316000", era="old", api_key=KEY)
        raise AssertionError("expected MurielValidationError")
    except MurielValidationError:
        pass


def test_cas_number_is_refused_locally():
    n = len(SENT)
    try:
        get_results(pwsid="IL0316000", cas_number="7439-92-1", api_key=KEY)
        raise AssertionError("expected MurielValidationError")
    except MurielValidationError:
        assert len(SENT) == n            # nothing was sent


def test_out_of_credits_is_a_credits_error_with_the_server_message():
    NEXT["resp"] = _Resp(402, {"detail": "Out of credits. Data calls cost 1 credit per "
                                         "1,000 records returned."})
    try:
        get_results(pwsid="IL0316000", api_key=KEY)
        raise AssertionError("expected MurielCreditsError")
    except MurielCreditsError as exc:
        msg = str(exc)
        assert exc.status_code == 402
        assert msg.startswith("Out of Muriel API credits") and "buy more credits" in msg
        assert "info@murielai.io" in msg and "nothing was charged" in msg
        assert "1,000 records" in exc.server_message
    finally:
        NEXT["resp"] = _Resp()


def test_not_held_is_a_server_error():
    NEXT["resp"] = _Resp(501, {"detail": "Violation records are not available yet."})
    try:
        muriel.get_violations(pwsid="IL0316000", api_key=KEY)
        raise AssertionError("expected MurielServerError")
    except MurielServerError as exc:
        assert exc.status_code == 501
    finally:
        NEXT["resp"] = _Resp()


def test_environment_supplies_key_and_base_url():
    old = {k: os.environ.get(k) for k in ("MURIEL_API_KEY", "MURIEL_BASE_URL")}
    os.environ["MURIEL_API_KEY"] = KEY
    os.environ["MURIEL_BASE_URL"] = "http://localhost:8000"
    try:
        NEXT["resp"] = _Resp(body={"systems": [], "records": []})
        SystemsClient().get_systems(state="DE")
        s = _last()
        assert s["key"] == KEY and s["url"].startswith("http://localhost:8000/api/v1/systems/")
        get_results(pwsid="DE0000001")
        assert _last()["url"].startswith("http://localhost:8000/")
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        NEXT["resp"] = _Resp()


def test_plain_http_is_refused_except_localhost():
    try:
        get_results(pwsid="IL0316000", api_key=KEY, base_url="http://api.murielai.io")
        raise AssertionError("expected MurielAPIError")
    except muriel.MurielAPIError as exc:
        assert "https" in str(exc)
    get_results(pwsid="IL0316000", api_key=KEY, base_url="http://127.0.0.1:8080")
    assert _last()["url"].startswith("http://127.0.0.1:8080/")


def test_redirects_are_not_followed():
    r = _Resp(302)
    r.headers = {"Location": "https://elsewhere.example/steal"}
    NEXT["resp"] = r
    try:
        get_results(pwsid="IL0316000", api_key=KEY)
        raise AssertionError("expected MurielAPIError")
    except muriel.MurielAPIError as exc:
        assert exc.status_code == 302 and "not followed" in str(exc)
    finally:
        NEXT["resp"] = _Resp()


def test_redirects_are_disabled_on_the_request():
    seen = {}
    def spy(self, method, url, **kw):
        seen.update(kw)
        return _Resp()
    real = requests.Session.request
    requests.Session.request = spy
    try:
        get_results(pwsid="IL0316000", api_key=KEY)
    finally:
        requests.Session.request = real
    assert seen.get("allow_redirects") is False


def test_systems_limit_none_pages_through_the_whole_state():
    from muriel.endpoints import systems as sysmod
    calls = []
    total = 5

    def paging(self, method, url, params=None, json=None, timeout=None, **kw):
        p = dict(params or {})
        calls.append(p)
        lo, n = int(p["offset"]), int(p["limit"])
        recs = [{"pwsid": f"IL{i:07d}"} for i in range(lo, min(lo + n, total))]
        return _Resp(body={"state": "IL", "records": recs, "systems": [r["pwsid"] for r in recs],
                           "system_count": len(recs), "total_systems": total,
                           "has_more": lo + len(recs) < total})

    real, old_page = requests.Session.request, sysmod.MAX_PAGE
    requests.Session.request, sysmod.MAX_PAGE = paging, 2
    try:
        resp = muriel.get_systems(state="il", limit=None, api_key=KEY)
        one = muriel.get_systems(state="IL", limit=2, offset=2, api_key=KEY)
    finally:
        requests.Session.request, sysmod.MAX_PAGE = real, old_page
    assert [c["offset"] for c in calls[:3]] == [0, 2, 4] and len(calls) == 4
    assert resp["system_count"] == resp["total_systems"] == 5
    assert len(set(resp["systems"])) == 5 and resp["has_more"] is False and resp["limit"] is None
    assert calls[-1] == {"limit": 2, "offset": 2} and one["system_count"] == 2


if __name__ == "__main__":
    import sys
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("PASS", name)
            except Exception as exc:  # noqa: BLE001
                failed += 1
                print("FAIL", name, repr(exc))
    print("\nALL TESTS PASS" if not failed else f"\n{failed} FAILED")
    sys.exit(1 if failed else 0)


# ---- limit=None and limits over 1,000 page for you ------------------------

def _paged(total, cap=None):
    """A fake server holding `total` records that pages like the API: at most
    1,000 a request, ordered, `pagination` on each response, and (for state
    and area routes) an offset cap."""
    def req(self, method, url, params=None, json=None, timeout=None, **kw):
        p = dict(params or {})
        SENT.append({"method": method, "url": url, "params": p, "key": self.headers.get("X-API-Key")})
        off, lim = int(p.get("offset", 0)), int(p["limit"])
        assert lim <= 1000, "the API rejects a limit over 1,000"
        n = max(0, min(lim, total - off))
        more = off + n < total
        capped = cap is not None and more and off + lim >= cap
        return _Resp(body={"records": [{"i": off + k} for k in range(n)],
                           "pagination": {"has_more": more and not capped,
                                          "offset_limit_reached": capped,
                                          "max_offset": cap or 1_000_000}})
    return req


def _with(fake, fn):
    saved = requests.Session.request
    requests.Session.request = fake
    try:
        return fn()
    finally:
        requests.Session.request = saved


def test_limit_none_returns_a_whole_system():
    SENT.clear()
    rows = _with(_paged(2_500), lambda: get_results(pwsid="IL0316000", limit=None, api_key=KEY))
    assert len(rows) == 2_500 and [r["i"] for r in rows] == list(range(2_500))
    assert [s["params"]["offset"] for s in SENT] == [0, 1000, 2000]
    assert all(s["params"]["limit"] == 1000 for s in SENT)
    assert all(s["url"].endswith("/api/v1/records/system/IL0316000") for s in SENT)


def test_limit_left_out_is_still_ten():
    SENT.clear()
    rows = _with(_paged(2_500), lambda: get_results(pwsid="IL0316000", api_key=KEY))
    assert len(rows) == 10 and len(SENT) == 1 and SENT[0]["params"]["limit"] == 10


def test_a_limit_over_1000_is_fetched_in_pages_and_stops_there():
    SENT.clear()
    rows = _with(_paged(5_000), lambda: get_results(pwsid="IL0316000", limit=2_500, api_key=KEY))
    assert len(rows) == 2_500
    assert [(s["params"]["offset"], s["params"]["limit"]) for s in SENT] == [(0, 1000), (1000, 1000), (2000, 500)]


def test_paging_starts_from_the_offset_given():
    SENT.clear()
    rows = _with(_paged(2_500), lambda: get_results(pwsid="IL0316000", limit=None, offset=1_500, api_key=KEY))
    assert len(rows) == 1_000 and rows[0]["i"] == 1_500


def test_a_state_query_stops_at_the_offset_cap_and_says_so():
    import pytest
    SENT.clear()
    with pytest.warns(UserWarning, match="Stopped at 3,000 records"):
        rows = _with(_paged(50_000, cap=3_000),
                     lambda: get_results(state="IL", analyte="Lead", limit=None, api_key=KEY))
    assert len(rows) == 3_000


def test_limit_zero_is_refused():
    import pytest
    with pytest.raises(MurielValidationError):
        get_results(pwsid="IL0316000", limit=0, api_key=KEY)


# ---- contaminant feeds: every record by default, through the API's cursor ----

def _cursor_feed(total, fail_once_at=None):
    """A fake feed route that pages with pagination.next_cursor (the offset,
    as a string) and, optionally, rate-limits one page once."""
    state = {"failed": False}

    def req(self, method, url, params=None, json=None, timeout=None, **kw):
        p = dict(params or {})
        SENT.append({"method": method, "url": url, "params": p, "key": self.headers.get("X-API-Key")})
        at, lim = int(p.get("cursor", 0)), int(p["limit"])
        assert lim <= 1000, "the API rejects a limit over 1,000"
        if fail_once_at is not None and at == fail_once_at and not state["failed"]:
            state["failed"] = True
            return _Resp(429, {"detail": "Rate limit: 60 requests a minute per key."})
        n = max(0, min(lim, total - at))
        more = at + n < total
        return _Resp(body={"records": [{"i": at + k} for k in range(n)],
                           "pagination": {"has_more": more,
                                          "next_cursor": str(at + n) if more else None}})
    return req


def test_a_feed_returns_every_record_when_no_limit_is_given():
    SENT.clear()
    rows = _with(_cursor_feed(2_500), lambda: get_lead(api_key=KEY))
    assert [r["i"] for r in rows] == list(range(2_500))
    assert [s["params"].get("cursor") for s in SENT] == [None, "1000", "2000"]
    assert all(s["params"]["limit"] == 1000 and s["url"].endswith("/api/v1/records/lead") for s in SENT)


def test_a_feed_with_limit_none_is_the_same():
    SENT.clear()
    rows = _with(_cursor_feed(1_200), lambda: get_lead(limit=None, api_key=KEY))
    assert len(rows) == 1_200 and len(SENT) == 2


def test_a_feed_limit_stops_there_and_filters_go_on_every_page():
    SENT.clear()
    rows = _with(_cursor_feed(5_000), lambda: get_lead(limit=1_500, min_concentration=0.015, api_key=KEY))
    assert len(rows) == 1_500
    assert [(s["params"].get("cursor"), s["params"]["limit"]) for s in SENT] == [(None, 1000), ("1000", 500)]
    assert all(s["params"]["min_concentration"] == 0.015 for s in SENT)


def test_a_rate_limited_page_is_retried_not_lost():
    from muriel import paging
    saved, paging.RATE_LIMIT_WAIT = paging.RATE_LIMIT_WAIT, 0
    try:
        SENT.clear()
        rows = _with(_cursor_feed(2_500, fail_once_at=1000), lambda: muriel.get_pfas(api_key=KEY))
    finally:
        paging.RATE_LIMIT_WAIT = saved
    assert len(rows) == 2_500 and len(SENT) == 4


def test_an_older_server_without_a_cursor_gives_one_page_not_a_loop():
    SENT.clear()
    old = lambda self, method, url, params=None, **kw: (
        SENT.append({"params": dict(params or {})}) or
        _Resp(body={"records": [{"i": k} for k in range(1000)], "pagination": None}))
    rows = _with(old, lambda: get_lead(api_key=KEY))
    assert len(rows) == 1000 and len(SENT) == 1


def test_an_analyte_group_query_follows_the_cursor():
    SENT.clear()
    rows = _with(_cursor_feed(2_100), lambda: get_results(analyte_group="pfas", limit=None, api_key=KEY))
    assert len(rows) == 2_100 and SENT[-1]["url"].endswith("/api/v1/records/group/pfas")


def test_a_feed_limit_of_zero_is_refused():
    import pytest
    with pytest.raises(MurielValidationError):
        get_lead(limit=0, api_key=KEY)


def test_a_rate_limit_error_says_how_long_to_wait():
    import pytest
    from muriel import MurielRateLimitError
    r = _Resp(429, {"detail": "Rate limit: 60 requests a minute per key. Wait and retry."})
    r.headers = {"Retry-After": "20"}
    NEXT["resp"] = r
    with pytest.raises(MurielRateLimitError) as info:
        get_results(pwsid="IL0316000", api_key=KEY)
    assert info.value.retry_after == 20 and info.value.status_code == 429
    NEXT["resp"] = _Resp()

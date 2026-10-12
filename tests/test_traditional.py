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
        assert exc.status_code == 402 and "1,000 records" in str(exc)
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

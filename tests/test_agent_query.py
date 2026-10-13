"""Agent.query / muriel.query: arguments, payload, and shaped answers.

No network: the HTTP session is replaced with a stub that records the
payload and returns a canned API response.

    python -m pytest tests/test_agent_query.py
    python tests/test_agent_query.py          # without pytest
"""
from datetime import date, datetime

from pydantic import BaseModel

import muriel
from muriel import agent as agent_mod
from muriel.agent import Agent
from muriel.exceptions import MurielAPIError, MurielValidationError
from muriel.models import AgentQueryResponse

EVENT = {
    "event_type": "new_results",
    "num_events": 1,
    "pwsid": "IL0316000",
    "insight": "Lead and copper results from 12 sites were posted today.",
    "extra": "dropped for a field-list schema",
}


class _Resp:
    def __init__(self, body, status=200):
        self._body, self.status_code, self.content = body, status, b"x"

    def json(self):
        return self._body


class _Session:
    def __init__(self, body):
        self.body, self.sent, self.headers = body, None, {}

    def post(self, url, json=None, timeout=None, **kw):
        self.url, self.sent = url, json
        return _Resp(self.body)

    def close(self):
        pass


def _agent(body=None):
    a = Agent(api_key="test-key", base_url="https://example.test")
    a._session = _Session(body if body is not None else
                          {"results": [EVENT], "count": 1, "summary": "s"})
    return a


def _raises(exc, fn):
    try:
        fn()
    except exc:
        return
    raise AssertionError(f"expected {exc.__name__}")


def test_plain_query_unchanged():
    a = _agent()
    r = a.query("Get the latest events for Chicago Water")
    assert isinstance(r, AgentQueryResponse) and r.count == 1
    assert a._session.sent == {"prompt": "Get the latest events for Chicago Water",
                               "max_records": 1000}
    assert a._session.url == "https://example.test/api/v1/agent/query"


def test_landing_page_call():
    a = _agent()
    r = a.query("Get the latest events for Chicago Water", pwsid="IL0316000",
                since="2026-09-29",
                schema=["event_type", "num_events", "pwsid", "insight"])
    sent = a._session.sent
    assert sent["pwsid"] == "IL0316000" and sent["since"] == "2026-09-29"
    assert sent["schema"]["required"] == ["event_type", "num_events", "pwsid", "insight"]
    assert sent["schema"]["additionalProperties"] is False
    # Exactly the requested keys, in the requested order.
    assert list(r) == ["event_type", "num_events", "pwsid", "insight"]
    assert r["num_events"] == 1


def test_since_accepts_dates_and_rejects_junk():
    a = _agent()
    a.query("x", since=date(2026, 9, 29))
    assert a._session.sent["since"] == "2026-09-29"
    a.query("x", since=datetime(2026, 9, 29, 13, 5))
    assert a._session.sent["since"] == "2026-09-29"
    _raises(MurielValidationError, lambda: a.query("x", since="last tuesday"))


def test_pwsid_normalised_and_validated():
    a = _agent()
    a.query("x", pwsid=" il0316000 ")
    assert a._session.sent["pwsid"] == "IL0316000"
    _raises(MurielValidationError, lambda: a.query("x", pwsid="Chicago"))


def test_schema_forms():
    class Ev(BaseModel):
        event_type: str
        num_events: int

    a = _agent()
    ev = a.query("x", schema=Ev)
    assert isinstance(ev, Ev) and ev.num_events == 1
    raw = a.query("x", schema={"type": "object"})
    assert raw["extra"].startswith("dropped")  # a JSON Schema dict returns the object as sent
    _raises(MurielValidationError, lambda: a.query("x", schema=[]))
    _raises(MurielValidationError, lambda: a.query("x", schema=["a", "a"]))
    _raises(MurielValidationError, lambda: a.query("x", schema="event_type"))


def test_missing_field_is_an_error_not_a_none():
    a = _agent({"results": [{"event_type": "new_results"}], "count": 1, "summary": ""})
    _raises(MurielAPIError, lambda: a.query("x", schema=["event_type", "insight"]))


def test_empty_prompt_rejected():
    _raises(MurielValidationError, lambda: _agent().query("  "))


def test_module_level_query_reuses_one_agent_per_key():
    a = _agent()
    agent_mod._agents[None] = a
    try:
        r = muriel.query("Get the latest events for Chicago Water",
                         pwsid="IL0316000", schema=["pwsid"])
        assert r == {"pwsid": "IL0316000"}
        assert a._session.sent["pwsid"] == "IL0316000"
    finally:
        agent_mod._agents.clear()


def test_module_level_query_takes_an_api_key():
    made = []
    real_init = Agent.__init__

    def fake_init(self, api_key=None, base_url=None, timeout=30):
        real_init(self, api_key=api_key, base_url="https://example.test")
        self._session = _Session({"results": [EVENT], "count": 1, "summary": ""})
        made.append(api_key)

    Agent.__init__ = fake_init
    try:
        muriel.query("x", api_key="key-one", since="2026-09-29")
        muriel.query("y", api_key="key-one")
        muriel.query("z", api_key="key-two")
        assert made == ["key-one", "key-two"]   # one Agent per key, reused
        assert agent_mod._agents["key-one"]._api_key == "key-one"
    finally:
        Agent.__init__ = real_init
        agent_mod._agents.clear()


def test_nested_model_and_a_wrapped_answer():
    from typing import List, Optional

    class Item(BaseModel):
        analyte: str
        limit: Optional[float]

    class Report(BaseModel):
        pwsid: str
        items: List[Item]

    wrapped = {"$parameter": {"pwsid": "IL0316000",
                              "items": [{"analyte": "LEAD", "limit": None}]}}
    a = _agent({"results": [wrapped], "count": 1, "summary": "s"})
    r = a.query("x", schema=Report)
    assert isinstance(r, Report) and r.items[0].analyte == "LEAD"
    assert "$defs" in a._session.sent["schema"]          # sent as Pydantic emits it


def test_an_answer_that_does_not_fit_the_model_says_so():
    class Report(BaseModel):
        pwsid: str
        results_over_mcl: int

    a = _agent({"results": [{"pwsid": "IL0316000"}], "count": 1, "summary": "s"})
    try:
        a.query("x", schema=Report)
        raise AssertionError("expected MurielAPIError")
    except MurielAPIError as e:
        assert "did not fit Report" in str(e) and "results_over_mcl" in str(e)
        assert e.response == {"pwsid": "IL0316000"}


def test_out_of_credits_reports_the_balance():
    a = _agent()
    body = {"detail": {"error": "out_of_credits", "message": "You are out of credits.",
                       "balance": 0, "contact": "info@murielai.io"}}
    a._session.post = lambda url, json=None, timeout=None, **kw: _Resp(body, 402)
    try:
        a.query("x")
        raise AssertionError("expected MurielCreditsError")
    except Exception as e:
        from muriel import MurielCreditsError
        assert isinstance(e, MurielCreditsError)
        assert e.balance == 0 and "(balance: 0)" in str(e)
        assert e.buy_url.startswith("mailto:info@murielai.io")


def test_every_error_status_raises_its_own_exception():
    from muriel.exceptions import (MurielAuthenticationError, MurielCreditsError,
                                   MurielRateLimitError, MurielServerError)
    cases = [(400, MurielValidationError), (401, MurielAuthenticationError),
             (402, MurielCreditsError), (429, MurielRateLimitError),
             (500, MurielServerError), (503, MurielServerError), (418, MurielAPIError)]
    for status, exc in cases:
        a = _agent()
        body = {"detail": f"server says {status}"}
        a._session.post = lambda url, json=None, timeout=None, _b=body, _s=status, **kw: _Resp(_b, _s)
        try:
            a.query("x")
            raise AssertionError(f"{status}: expected {exc.__name__}")
        except exc as e:
            assert type(e) is exc, f"{status}: got {type(e).__name__}"
            assert e.status_code == status
            if status == 402:
                assert str(e).startswith("Out of Muriel API credits")
                assert "info@murielai.io" in str(e) and e.server_message == "server says 402"
            elif status in (429, 500, 503):
                assert "server says" in str(e), f"{status}: server detail lost"


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print("ok ", name)
    print(f"{n} passed")

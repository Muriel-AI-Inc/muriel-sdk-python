"""
Agent Mode for natural language water quality queries.

Calls POST /api/v1/agent/query on the Muriel API. All LLM reasoning
happens server-side — users only need a Muriel API key.
"""

import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Sequence, Type, TypeVar, Union

import requests
from pydantic import BaseModel

from .config import AGENT_TIMEOUT, checked_base_url, get_api_key, get_base_url
from .exceptions import (
    MurielAPIError,
    MurielAuthenticationError,
    MurielCreditsError,
    MurielRateLimitError,
    MurielServerError,
    MurielValidationError,
    detail_of,
)
from .models import AgentQueryResponse

T = TypeVar("T", bound=BaseModel)

# What `schema=` accepts: a Pydantic model, a list of field names, or a JSON
# Schema dict. The API only ever sees a JSON Schema dict.
SchemaArg = Union[Type[BaseModel], Sequence[str], Dict[str, Any]]

# Nine characters: a state code (or two digits for EPA-region tribal systems),
# then seven characters that are nearly always digits.
_PWSID_RE = re.compile(r"^(?:[A-Z]{2}|\d{2})(?=[A-Z0-9]*\d)[A-Z0-9]{7}$")


def _fields_schema(fields: Sequence[str]) -> Dict[str, Any]:
    """JSON Schema for an object with exactly these fields, all required."""
    names = [str(f).strip() for f in fields]
    if not names or any(not n for n in names):
        raise MurielValidationError("schema= needs at least one non-empty field name.")
    if len(set(names)) != len(names):
        raise MurielValidationError("schema= lists the same field twice.")
    return {
        "type": "object",
        "properties": {n: {} for n in names},
        "required": names,
        "additionalProperties": False,
    }


def _normalise_since(since: Union[str, date, datetime, None]) -> Optional[str]:
    """ISO date string, or None. Accepts a date, a datetime, or 'YYYY-MM-DD'."""
    if since is None:
        return None
    if isinstance(since, datetime):
        return since.date().isoformat()
    if isinstance(since, date):
        return since.isoformat()
    text = str(since).strip()
    try:
        return date.fromisoformat(text[:10]).isoformat()
    except ValueError:
        raise MurielValidationError(
            f"since= must be a date or 'YYYY-MM-DD', got {since!r}."
        ) from None


class Agent:
    """
    Natural language interface to the Muriel water quality database.

    Sends queries to the Muriel API's server-side agent endpoint.
    Only a Muriel API key is required — no separate LLM key needed.

    Usage::

        from muriel import Agent

        agent = Agent()  # reads MURIEL_API_KEY from environment
        response = agent.query("Show me PFAS levels in Illinois")
        print(response.summary)
        print(response.results)

    Pass a Pydantic model as ``schema`` to receive a typed, validated object::

        from pydantic import BaseModel
        from muriel import Agent

        class PFASResult(BaseModel):
            pwsid: str
            analyte: str
            concentration: float

        agent = Agent()
        result = agent.query("PFAS in IL", schema=PFASResult)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = AGENT_TIMEOUT,
    ):
        """
        Initialise the Agent.

        Args:
            api_key:  Muriel API key. Defaults to the ``MURIEL_API_KEY``
                      environment variable.
            base_url: Override the API base URL (default: https://api.murielai.io).
            timeout:  HTTP timeout in seconds (default: 120). An agent
                      question typically takes 10-60 seconds; the server
                      always answers within about 100.
        """
        self._api_key = api_key or get_api_key()
        if not self._api_key:
            raise MurielAuthenticationError(
                "API key is required. Pass it as api_key= or set the "
                "MURIEL_API_KEY environment variable."
            )
        self._base_url = checked_base_url(base_url or get_base_url())
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({
            "X-API-Key": self._api_key,
            "Content-Type": "application/json",
        })

    # ── Public interface ───────────────────────────────────────────────────────

    def query(
        self,
        prompt: str,
        *,
        pwsid: Optional[str] = None,
        since: Union[str, date, datetime, None] = None,
        schema: Optional[SchemaArg] = None,
        max_records: int = 1000,
    ) -> Union[AgentQueryResponse, Dict[str, Any], T]:
        """
        Query water quality data using natural language.

        Args:
            prompt:      Plain-English description of the data you want.
            pwsid:       Optional Public Water System ID (e.g. ``"IL0316000"``).
                         Pins the question to one system, so the agent does
                         not have to work out which system a name means.
            since:       Optional date (``date``, ``datetime`` or
                         ``"YYYY-MM-DD"``). Only results and events on or
                         after this date -- what an app polling for new
                         activity needs.
            schema:      Optional shape for the answer. One of:

                         * a list of field names, e.g.
                           ``["event_type", "num_events", "pwsid", "insight"]``
                           -- returns a plain ``dict`` with exactly those keys;
                         * a Pydantic model -- returns an instance of it;
                         * a JSON Schema ``dict`` -- returns a plain ``dict``.
            max_records: Cap on the number of records returned (default 1000,
                         max 10000).

        Returns:
            ``AgentQueryResponse`` with ``results``, ``count``, ``summary``,
            ``execution_log``, and an optional ``warning`` when no schema is
            given. With a schema, the shaped answer: a ``dict`` for a field
            list or JSON Schema, a model instance for a Pydantic model.

        Example::

            import muriel

            muriel.query(
                "Get the latest events for Chicago Water",
                api_key="YOUR_MURIEL_API_KEY",
                since="2026-09-29",
                schema=["event_type", "num_events", "pwsid", "insight"],
            )

        Raises:
            MurielAuthenticationError: Invalid or missing API key.
            MurielRateLimitError:      Credit balance exhausted.
            MurielServerError:         Server-side error.
            MurielAPIError:            Any other failure.
        """
        if not isinstance(prompt, str) or not prompt.strip():
            raise MurielValidationError("prompt must be a non-empty string.")

        payload: Dict[str, Any] = {
            "prompt": prompt,
            "max_records": max_records,
        }

        if pwsid is not None:
            pwsid = str(pwsid).strip().upper()
            if not _PWSID_RE.match(pwsid):
                raise MurielValidationError(
                    f"pwsid= should look like 'IL0316000' (state code, then the "
                    f"system number), got {pwsid!r}."
                )
            payload["pwsid"] = pwsid
        since_iso = _normalise_since(since)
        if since_iso is not None:
            payload["since"] = since_iso

        model: Optional[Type[BaseModel]] = None
        fields: Optional[List[str]] = None
        if schema is not None:
            if isinstance(schema, type) and issubclass(schema, BaseModel):
                model = schema
                payload["schema"] = schema.model_json_schema()
            elif isinstance(schema, dict):
                payload["schema"] = schema
            elif isinstance(schema, (list, tuple)):
                payload["schema"] = _fields_schema(schema)
                fields = list(payload["schema"]["required"])
            else:
                raise MurielValidationError(
                    "schema= must be a list of field names, a Pydantic model, "
                    "or a JSON Schema dict."
                )

        data = self._post("/api/v1/agent/query", payload)

        if schema is not None:
            # The API has already shaped the results; take the first shaped
            # object, as the Pydantic path always has.
            results = data.get("results", [])
            first = results[0] if isinstance(results, list) and results else results
            if model is not None:
                return model.model_validate(first)
            first = dict(first or {})
            if fields is not None:
                missing = [f for f in fields if f not in first]
                if missing:
                    raise MurielAPIError(
                        f"The answer is missing requested field(s): {', '.join(missing)}."
                    )
                return {f: first[f] for f in fields}
            return first

        return AgentQueryResponse(
            results=data.get("results", []),
            count=data.get("count", 0),
            summary=data.get("summary", ""),
            execution_log=data.get("execution_log", []),
            warning=data.get("warning"),
            documents=data.get("documents") or [],
            credits=data.get("credits"),
        )

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self._session.close()

    def __enter__(self) -> "Agent":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    # ── Internal ───────────────────────────────────────────────────────────────

    def _post(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self._base_url}{endpoint}"
        try:
            # No redirects: the key travels in X-API-Key, which requests would
            # forward to whatever host a redirect names.
            response = self._session.post(url, json=payload, timeout=self._timeout,
                                          allow_redirects=False)
        except requests.exceptions.Timeout:
            raise MurielAPIError(
                f"No answer within {self._timeout}s. The server answers within "
                "about 100 seconds, so if you lowered timeout=, raise it; "
                "otherwise try again or ask a narrower question."
            )
        except requests.exceptions.ConnectionError:
            raise MurielAPIError(f"Failed to connect to {self._base_url}")
        except requests.exceptions.RequestException as e:
            raise MurielAPIError(f"Request failed: {e}")

        if 300 <= response.status_code < 400:
            raise MurielAPIError(
                f"Unexpected redirect ({response.status_code}); not followed, so your "
                "API key was not sent elsewhere. Check MURIEL_BASE_URL.",
                status_code=response.status_code,
            )
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            raise MurielAuthenticationError(
                "Invalid API key.",
                status_code=401,
                response=response.json() if response.content else None,
            )
        elif response.status_code == 400:
            error = response.json() if response.content else {}
            raise MurielValidationError(
                error.get("detail", "Validation error"),
                status_code=400,
                response=error,
            )
        elif response.status_code == 402:
            raise MurielCreditsError(
                detail_of(response, ""),
                status_code=402,
                response=response.json() if response.content else None,
            )
        elif response.status_code == 429:
            raise MurielRateLimitError(
                detail_of(response, "Rate limit exceeded. Wait and retry."),
                status_code=429,
                response=response.json() if response.content else None,
            )
        elif response.status_code in (504, 524):
            raise MurielServerError(
                "The question took longer than one API call allows. Ask a narrower "
                "question (one system, one contaminant or a date range) and retry.",
                status_code=response.status_code,
            )
        elif response.status_code >= 500:
            raise MurielServerError(
                detail_of(response, "Server error during agent query."),
                status_code=response.status_code,
                response=response.json() if response.content else None,
            )
        else:
            raise MurielAPIError(
                f"Unexpected status {response.status_code}",
                status_code=response.status_code,
            )


# ── Module-level convenience ───────────────────────────────────────────────────

# One Agent per API key, so repeated calls reuse a connection. `None` is the
# key read from MURIEL_API_KEY.
_agents: Dict[Optional[str], Agent] = {}


def query(
    prompt: str,
    *,
    api_key: Optional[str] = None,
    pwsid: Optional[str] = None,
    since: Union[str, date, datetime, None] = None,
    schema: Optional[SchemaArg] = None,
    max_records: int = 1000,
) -> Union[AgentQueryResponse, Dict[str, Any], BaseModel]:
    """``muriel.query(...)``: ``Agent.query`` without building an Agent.

    Args:
        api_key: Muriel API key. Defaults to the ``MURIEL_API_KEY``
                 environment variable. All other arguments are as for
                 ``Agent.query``.

    Build an ``Agent`` yourself to set a base URL or timeout.
    """
    agent = _agents.get(api_key)
    if agent is None:
        agent = _agents[api_key] = Agent(api_key=api_key)
    return agent.query(
        prompt, pwsid=pwsid, since=since, schema=schema, max_records=max_records
    )

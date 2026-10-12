# Muriel Python SDK

`muriel` is the official Python package for [Muriel](https://murielai.io), the
AI agent for U.S. drinking water data. It gives your code the same two things
the Muriel app gives a person: answers to plain-English questions about any
public water system, and direct access to the sample results those answers are
built from.

```bash
pip install muriel
```

## What this package does

**It puts the Muriel agent in your code.** `muriel.query("...")` sends a
question to the same agent that answers at murielai.io. The agent works out
which systems, contaminants and dates the question is about, pulls the
results, checks them against federal limits (MCLs, action levels, treatment
rules), and returns:

- a plain-English answer,
- the records it used, as a list you can loop over,
- any CSV or PDF it produced when you asked for one,
- a caveat when the data needs one, such as a state that has stopped updating,
- and what the question cost.

Give it a JSON schema, a list of field names or a Pydantic model, and the
answer comes back in exactly that shape, ready for a database, a dashboard or
another program. Scope any question to one water system (`pwsid=`) or a start
date (`since=`).

**It gives you the data directly, too.** When you already know what you want,
such as one system's full history, one contaminant across the country, every
water system in a state, or the results for the system serving an address,
functions like `get_results()`, `get_lead()` and `get_systems()` return the
records themselves, with filters for dates, detections, concentrations and
contaminant groups, and paging for large pulls. Every record has the same
fields whichever state it came from, with values as published and converted
to mg/L so they compare across states.

**One key, one balance, plain Python.** Both halves use the same API key and
the same credits as your Muriel account. Results come back as ordinary
dictionaries and lists, or as typed Pydantic models for agent answers. Errors
are typed exceptions you can catch, such as out of credits, an invalid key or
a bad parameter, each with the server's explanation. Keys are only ever sent
over HTTPS and never forwarded on a redirect.

Use the agent for questions, summaries, comparisons and anything you would
otherwise ask an analyst. Use the direct functions for repeatable pipelines,
bulk pulls and exact filters.

## What Muriel is

Muriel reads the drinking water monitoring results states publish, standardized
into one record, and checks them against federal limits. Every answer is built
from the sample results themselves, not from summaries or annual reports, and
shows its work: the rows it used and how current each state is. A gap is never
passed off as a clean record.

- **88 million+ results** from **32 states** and **63,000+ water systems**
- **Current:** many states update daily, often within days of sampling
- **Deep:** some states go back to the 1970s
- **Every contaminant states test for:** lead and copper, PFAS, nitrate,
  disinfection byproducts, arsenic, coliform, VOCs and more

See exactly which states, contaminants and years are covered, live, at
[murielai.io/overview](https://murielai.io/overview).

It is built for people who work with drinking water: utilities and the
regulators who oversee them, and the labs, engineering firms and vendors who
serve them.

## Get a key

Create an API key on your [account page](https://murielai.io/account), then:

```bash
export MURIEL_API_KEY="muriel_live_..."
```

Every function reads `MURIEL_API_KEY`; you can also pass `api_key=` directly.

## Ask the agent

```python
import muriel

answer = muriel.query("Is Chicago's water meeting federal limits for lead and copper?")

print(answer.summary)                 # the answer, in plain English
for r in answer.results[:5]:          # the records it rests on
    print(r["sample_collection_date"], r["system_name"],
          r["result_analyte_name"], r["result_value"], r["result_unit"])
```

The agent is the same one that answers at [murielai.io](https://murielai.io).
It finds the system, pulls the results, compares them with MCLs, action levels
and treatment rules, and tells you when a state's data is out of date.

### What you can ask

| | |
|---|---|
| **Compliance** | Which systems in Georgia had a nitrate result above the MCL in the last year? |
| **Trends** | Which systems are within 20% of an MCL and trending up? |
| **PFAS** | Where has PFOA or PFOS been detected above 4 ppt in Pennsylvania? |
| **What changed** | What new results were published in California this week? |
| **Market research** | Which Illinois systems serving over 50,000 people have detected PFAS? |

### Scope it

```python
answer = muriel.query("Any new detections?", pwsid="IL0316000", since="2026-01-01")
```

### Get exactly the fields you need

Pass a list of field names, or a Pydantic model, and the answer comes back in
that shape:

```python
latest = muriel.query(
    "What was the most recent lead result for Chicago?",
    pwsid="IL0316000",
    schema=["sample_date", "result", "units", "above_action_level"],
)
```

```python
from typing import List
from pydantic import BaseModel
from muriel import Agent

class SystemSummary(BaseModel):
    pwsid: str
    system_name: str
    total_samples: int
    contaminants_found: List[str]

summary = Agent().query("Summarize water quality for IL0316000.", schema=SystemSummary)
print(summary.system_name, summary.total_samples)
```

### From question to CSV

Ask for an export and the file comes back with the answer:

```python
answer = muriel.query("Which systems in Oregon have a lead 90th percentile above 10 ppb? "
                      "Export it to a CSV, largest systems first.")
for doc in answer.documents:
    print(doc["filename"], doc["url"])
```

Each answer also carries `execution_log` (the steps the agent took), `warning`
(when the answer needs a caveat) and `credits` (what the question used).

## Query the data directly

When you know exactly what you want, such as one system's full history or one
contaminant across the country, call the data directly:

```python
from muriel import get_results, get_lead, get_systems

# One water system, history included
rows = get_results(pwsid="IL0316000", analyte="Lead", limit=100)

# A whole state, or one group of contaminants
rows = get_results(state="IL", analyte_group="pfas", limit=500)

# The water system that serves an address, then systems nearby
rows = get_results(address="121 N LaSalle St, Chicago, IL", radius_miles=10)

# The latest lead results nationwide
rows = get_lead(limit=50, detections_only=True)

# Every water system in a state, with size and latest sample
systems = get_systems(state="IL")
```

Every record carries the system, contaminant, value as published, the value in
mg/L, the sample date and place where known, and `era`: `"recent"` for the
window states currently publish, `"historical"` for the archive. Pass
`era="all"` to include history in the national feeds, or `era="recent"` to
limit a system or state query to current results.

| Function | What it returns |
|---|---|
| `get_results()` | Results by system, state, analyte group or address, with filters for dates, detections, concentration and analyte |
| `get_latest()`, `get_lead()`, `get_pfas()`, `get_coliform()`, `get_nitrate()`, `get_dbps()`, `get_arsenic()`, `get_manganese()`, `get_vocs()` | The latest results for one contaminant, nationwide |
| `get_systems()` | Water systems in a state |
| `get_state_sampling_points()`, `get_sampling_point_geocoding()` | Sampling points with a location |
| `get_state_facilities()`, `get_facility_geocoding()` | Facilities with a location, where states publish them |
| `SamplesClient`, `SystemsClient` | The same calls as objects |

Up to 1,000 records per call; page with `offset`. Monitoring requirements and
violation records (`get_requirements`, `get_violations`) are not available yet;
ask the agent about monitoring gaps and exceedances instead.

## Pricing

One balance of credits covers the app, this SDK and the MCP connector:

- **An agent question** is metered like a question in the app: typically
  1–3 credits, never more than 8.
- **A direct data call** costs 1 credit per 1,000 records returned, added up
  across calls. A call that returns nothing is free.

Every account gets 8 free credits a month. For more, email
[info@murielai.io](mailto:info@murielai.io).

## Errors

```python
from muriel import MurielAPIError, MurielCreditsError, get_results

try:
    rows = get_results(pwsid="IL0316000")
except MurielCreditsError:
    print("Out of credits.")
except MurielAPIError as e:
    print(e.status_code, e.message)
```

| Exception | When |
|---|---|
| `MurielAuthenticationError` | Missing or invalid API key (401) |
| `MurielValidationError` | A bad parameter (400) |
| `MurielCreditsError` | Out of credits (402); nothing was charged |
| `MurielNotFoundError` | Unknown system or resource (404) |
| `MurielRateLimitError` | Too many requests (429); wait and retry |
| `MurielServerError` | Not available (501), or a server error worth retrying (5xx) |

All of them inherit from `MurielAPIError`.

## Good to know

Muriel is a research and analysis tool, not a compliance determination.
Results are as states published them; coverage varies by state, and the
absence of a result is never evidence of compliance. Only your state primacy
agency can say whether a system is in compliance.

## Documentation

- Guides and SDK reference: [docs.murielai.io](https://docs.murielai.io)
- API reference: [api.murielai.io/docs](https://api.murielai.io/docs)
- Use Muriel in Claude, Cursor and other AI tools: [murielai.io/developers](https://murielai.io/developers)

## Support

- Email: [info@murielai.io](mailto:info@murielai.io)
- Issues: [github.com/Muriel-AI-Inc/muriel-sdk-python/issues](https://github.com/Muriel-AI-Inc/muriel-sdk-python/issues)

## License

MIT. Copyright (c) 2024-2026 Muriel AI, Inc. Use of the Muriel API is governed
by the terms at [murielai.io/terms](https://murielai.io/terms).

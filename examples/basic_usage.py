"""Muriel SDK examples: ask the agent first, query directly when you need to.

Set your key once and every call picks it up:

    export MURIEL_API_KEY=muriel_live_...      # from https://murielai.io/account

What it costs (one price list for the app, the API and the MCP connector):
  * an agent question is metered like a question in the app: typically 1-3
    credits, never more than 8;
  * a traditional data call costs 1 credit per 1,000 records returned, added
    up across calls -- the 10-record lookups below cost a hundredth of a
    credit each.
Every account gets 8 free credits a month. Out of credits raises
MurielCreditsError before anything runs.
"""
from typing import List

from pydantic import BaseModel

import muriel
from muriel import Agent, MurielCreditsError, get_lead, get_results


# ------------------------------------------------------------------ agent --

def example_1_ask():
    """Ask a question in plain English."""
    print("1. Ask the agent")
    r = muriel.query("What are the latest lead results for Chicago (IL0316000)?")
    print(f"   {r.summary}")
    print(f"   {r.count} records; this question used {r.credits['charged']} credits, "
          f"{r.credits['balance']} left")
    for step in r.execution_log:
        print(f"   tool: {step['tool']}")


def example_2_scope():
    """Scope a question to one system and a start date."""
    print("2. Scoped question")
    r = muriel.query("Any new detections?", pwsid="IL0316000", since="2026-01-01")
    print(f"   {r.summary}")
    if r.warning:
        print(f"   caveat: {r.warning}")


class SystemSummary(BaseModel):
    pwsid: str
    system_name: str
    total_samples: int
    contaminants_found: List[str]


def example_3_structured():
    """Get the answer back in exactly the shape your code wants."""
    print("3. Structured output")
    agent = Agent()                                   # reads MURIEL_API_KEY
    s = agent.query("Summarize water quality for IL0316000: total samples and "
                    "every contaminant detected.", schema=SystemSummary)
    print(f"   {s.system_name} ({s.pwsid}): {s.total_samples} samples")
    print(f"   detected: {', '.join(s.contaminants_found[:10])}")


# ------------------------------------------------------------ traditional --

def example_4_system_results():
    """Exact, parameter-driven: one system's lead results, history included."""
    print("4. Traditional: a system's results")
    rows = get_results(pwsid="IL0316000", analyte="Lead", limit=10)
    for row in rows[:5]:
        print(f"   {row['sample_collection_date']}  {row['result_analyte_name']}: "
              f"{row['result_value']} {row['result_unit'] or ''}  ({row['era']})")


def example_5_near_an_address():
    """Results from systems near a street address, nearest first."""
    print("5. Traditional: near an address")
    rows = get_results(address="233 S Wacker Dr, Chicago, IL 60606", radius_miles=10, limit=10)
    for row in rows[:5]:
        print(f"   {row.get('distance_miles')} mi  {row['system_name']}  "
              f"{row['result_analyte_name']}")


def example_6_national_feed():
    """The latest lead results across the country (the recent era by default)."""
    print("6. Traditional: national lead feed")
    rows = get_lead(limit=10, detections_only=True)
    for row in rows[:5]:
        print(f"   {row['state']}  {row['system_name']}: {row['result_value']} "
              f"{row['result_unit'] or ''}")


if __name__ == "__main__":
    try:
        for ex in (example_1_ask, example_2_scope, example_3_structured,
                   example_4_system_results, example_5_near_an_address,
                   example_6_national_feed):
            ex()
            print()
    except MurielCreditsError as exc:
        print(f"Out of credits: {exc}")

"""Call every public SDK function against the live API and report what works.

    cd muriel-sdk-python
    export MURIEL_API_KEY=muriel_live_...
    python tools/check_live_api.py            # everything except the agent
    python tools/check_live_api.py --agent    # also one small agent query (uses credits)

For each function: OK / EMPTY / FAIL, how many rows came back, the newest
date found in them, and how long it took. Writes the same thing to
tools/live_api_report.json so the docs can be corrected from evidence, not
from what the code says should exist.

Read-only: every call here is a GET except the optional agent query.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))            # the SDK in this repo, not a pip copy

import muriel  # noqa: E402

PWSID = os.getenv("CHECK_PWSID", "IL0316000")    # Chicago
STATE = os.getenv("CHECK_STATE", "IL")
N = 5


def rows_of(got):
    """A list of records, however the function returned them."""
    if got is None:
        return []
    if isinstance(got, list):
        return got
    if isinstance(got, dict):
        for k in ("results", "records", "data", "items", "systems", "violations",
                  "requirements", "facilities", "sampling_points"):
            if isinstance(got.get(k), list):
                return got[k]
        return [got]
    for k in ("results", "records", "data"):
        v = getattr(got, k, None)
        if isinstance(v, list):
            return v
    return [got]


def newest_date(rows):
    best = None
    for r in rows[:5000]:
        d = r if isinstance(r, dict) else getattr(r, "__dict__", {})
        for k, v in (d or {}).items():
            if "date" in k.lower() and isinstance(v, str) and len(v) >= 10 and v[:4].isdigit():
                if best is None or v[:10] > best:
                    best = v[:10]
    return best


def keys_of(rows):
    r = rows[0] if rows else None
    if isinstance(r, dict):
        return sorted(r.keys())[:25]
    return sorted(getattr(r, "__dict__", {}).keys())[:25] if r is not None else []


CHECKS = [
    # Traditional API -- results
    ("get_results(pwsid)", lambda: muriel.get_results(pwsid=PWSID, limit=N)),
    ("get_results(state)", lambda: muriel.get_results(state=STATE, limit=N)),
    ("get_results(analyte_group=pfas)", lambda: muriel.get_results(analyte_group="pfas", limit=N)),
    ("get_results(address)", lambda: muriel.get_results(address="121 N LaSalle St, Chicago, IL", limit=N)),
    ("get_latest", lambda: muriel.get_latest(limit=N)),
    ("get_lead", lambda: muriel.get_lead(limit=N)),
    ("get_pfas", lambda: muriel.get_pfas(limit=N)),
    ("get_coliform", lambda: muriel.get_coliform(limit=N)),
    ("get_nitrate", lambda: muriel.get_nitrate(limit=N)),
    ("get_dbps", lambda: muriel.get_dbps(limit=N)),
    ("get_arsenic", lambda: muriel.get_arsenic(limit=N)),
    ("get_manganese", lambda: muriel.get_manganese(limit=N)),
    ("get_vocs", lambda: muriel.get_vocs(limit=N)),
    # Systems, requirements, violations
    ("get_systems(state)", lambda: muriel.get_systems(state=STATE, limit=N)),
    ("get_requirements(pwsid)", lambda: muriel.get_requirements(pwsid=PWSID, limit=N)),
    ("get_requirements(state)", lambda: muriel.get_requirements(state=STATE, limit=N)),
    ("get_violations(pwsid)", lambda: muriel.get_violations(pwsid=PWSID, limit=N)),
    ("get_violations(state)", lambda: muriel.get_violations(state=STATE, limit=N)),
    # Facilities and sampling points
    ("get_state_facilities", lambda: muriel.get_state_facilities(state=STATE, limit=N)),
    ("get_state_sampling_points", lambda: muriel.get_state_sampling_points(state=STATE, limit=N)),
    # OO clients
    ("SamplesClient.get_samples", lambda: muriel.SamplesClient().get_samples(pwsid=PWSID)),
    ("SystemsClient.get_systems", lambda: muriel.SystemsClient().get_systems(state=STATE, limit=N)),
    ("RequirementsClient.get_requirements",
     lambda: muriel.RequirementsClient().get_requirements(pwsid=PWSID, limit=N)),
]

AGENT = [
    ("query() -- agent",
     lambda: muriel.query("Show me the latest lead samples in Illinois", max_records=5)),
]


def main() -> int:
    if not os.getenv("MURIEL_API_KEY"):
        print("Set MURIEL_API_KEY first.")
        return 2
    checks = CHECKS + (AGENT if "--agent" in sys.argv else [])
    base = os.getenv("MURIEL_BASE_URL", "https://api.murielai.io")
    print(f"Checking {len(checks)} functions against {base}\n")
    report = {"base_url": base, "pwsid": PWSID, "state": STATE,
              "at": time.strftime("%Y-%m-%dT%H:%M:%S"), "checks": []}
    # Geocoding needs a real facility and sample point; take them from the
    # state listing if it worked.
    facility_rows = []
    for name, fn in checks:
        t0 = time.time()
        entry = {"name": name}
        try:
            got = fn()
            rows = rows_of(got)
            if name == "get_state_facilities":
                facility_rows = rows
            entry.update(status="OK" if rows else "EMPTY", rows=len(rows),
                         newest=newest_date(rows), keys=keys_of(rows))
        except Exception as exc:  # noqa: BLE001 -- the point is to record it
            entry.update(status="FAIL", error=f"{type(exc).__name__}: {str(exc)[:300]}")
        entry["seconds"] = round(time.time() - t0, 2)
        report["checks"].append(entry)
        line = f"{entry['status']:<5} {name:<42} {entry['seconds']:>6}s"
        if entry["status"] != "FAIL":
            line += f"  rows={entry['rows']}" + (f"  newest={entry['newest']}" if entry.get("newest") else "")
        else:
            line += f"  {entry['error'][:110]}"
        print(line)

    # One geocoding call each, if a facility is known.
    fac = next((r for r in facility_rows if isinstance(r, dict) and r.get("pwsid")
                and (r.get("facility_id") or r.get("facilityid"))), None)
    if fac:
        extra = [("get_facility_geocoding",
                  lambda: muriel.get_facility_geocoding(
                      pwsid=fac["pwsid"], facility_id=fac.get("facility_id") or fac.get("facilityid")))]
        for name, fn in extra:
            t0 = time.time()
            entry = {"name": name}
            try:
                got = fn()
                rows = rows_of(got)
                entry.update(status="OK" if rows else "EMPTY", rows=len(rows), keys=keys_of(rows))
            except Exception as exc:  # noqa: BLE001
                entry.update(status="FAIL", error=f"{type(exc).__name__}: {str(exc)[:300]}")
            entry["seconds"] = round(time.time() - t0, 2)
            report["checks"].append(entry)
            print(f"{entry['status']:<5} {name:<42} {entry['seconds']:>6}s")
    else:
        print("skip  get_facility_geocoding / get_sampling_point_geocoding (no facility to try)")

    out = ROOT / "tools" / "live_api_report.json"
    out.write_text(json.dumps(report, indent=1))
    bad = [c["name"] for c in report["checks"] if c["status"] != "OK"]
    print(f"\n{len(report['checks']) - len(bad)} OK, {len(bad)} not OK. Report: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# Muriel Python SDK

Official Python SDK for the Muriel® Water Quality API.

## Installation

```bash
pip install muriel
```

## Quick start: ask the agent

Get an API key at https://murielai.io/account, then:

```bash
export MURIEL_API_KEY="muriel_live_..."
```

```python
import muriel

answer = muriel.query("Show me the latest lead samples in Illinois")
print(answer.summary)                 # the agent's answer
for r in answer.results[:5]:          # the records it rests on
    print(r["sample_collection_date"], r["system_name"], r["result_value"], r["result_unit"])

# Scope it and shape it
latest = muriel.query(
    "What was the most recent lead result for Chicago Water?",
    pwsid="IL0316000",
    schema=["sample_date", "result", "units", "above_action_level"],
)
```

One price list covers the app, this SDK and the MCP connector, from one balance of
credits: an agent question is metered like a question in the app (typically 1-3
credits, never more than 8), and the traditional functions below cost 1 credit per
1,000 records returned, added up across calls. Every account gets 8 free credits a
month. Out of credits raises `muriel.MurielCreditsError` before anything runs.

## Traditional API

```python
from muriel import get_results

results = get_results(pwsid="IL0316000", limit=50)            # history included
recent = get_results(state="IL", limit=100, era="recent")     # current window only
```

`get_requirements` and `get_violations` return HTTP 501: that data is not in the store yet.

Interactive API reference: https://api.murielai.io/docs. Guides: the muriel-sdk-docs site.

### Agent Mode (Recommended)

Use natural language to query water quality data:

```python
from muriel import Agent

agent = Agent(api_key='YOUR_API_KEY')

# Query using natural language
results = agent.query('Tell me where PFAS concentrations are rising')

print(results)
```

### Query by Address

```python
from muriel import get_results

# Find water quality data near a specific address
results = get_results(
    address='233 S Wacker Dr, Chicago, IL 60606',
    api_key='YOUR_API_KEY',
    radius_miles=10
)
```

### Filter by Analyte

```python
from muriel import get_results

# Get lead test results for a water system
results = get_results(
    pwsid='IL0316000',
    api_key='YOUR_API_KEY',
    analyte='Lead',
    num=50
)
```

### Query by Analyte Group

```python
from muriel import get_results

# Get all PFAS results
pfas_results = get_results(
    api_key='YOUR_API_KEY',
    analyte_group='pfas',
    num=100
)
```

## Features

- 🔍 **Simple API**: Easy-to-use functions for common queries
- 🤖 **Agent Mode**: Natural language queries powered by AI
- 📊 **Structured Data**: Pydantic models for type safety
- 🗺️ **Geographic Queries**: Search by address or coordinates
- 🔐 **Secure**: API key authentication
- ⚡ **Fast**: Efficient HTTP client with connection pooling

## Data Coverage

- **56,180+ Public Water Systems** across 31 states
- **40+ Million water quality records**
- **171,073 Sampling points** with geocoding
- **1,474 Unique analytes** including PFAS, lead, bacteria
- **20 Analyte groups** (PFAS, metals, microbial, VOCs, etc.)

## Advanced Usage

### Get Facilities with Geocoding

```python
from muriel import get_state_facilities

facilities = get_state_facilities(
    state='IL',
    api_key='YOUR_API_KEY',
    limit=100
)

for facility in facilities['facilities']:
    if facility.get('geocoding'):
        print(f"{facility['pwsid']}: {facility['geocoding']['address_formatted']}")
```

### Get Sampling Points

```python
from muriel import get_state_sampling_points

sampling_points = get_state_sampling_points(
    state='IL',
    api_key='YOUR_API_KEY',
    limit=100
)
```

### Agent Mode with Schema

```python
from muriel import Agent
from pydantic import BaseModel, Field
from typing import List

agent = Agent(api_key='YOUR_API_KEY')

class WaterQualitySummary(BaseModel):
    pwsid: str
    system_name: str
    total_samples: int
    contaminants_found: List[str]

result = agent.query(
    schema=WaterQualitySummary,
    prompt="Get a summary of water quality for Public Water System IL0316000"
)

print(f"System: {result.system_name}")
print(f"Total Samples: {result.total_samples}")
```

## API Reference

### Core Functions

- `get_results()` - Query water quality sample results
- `get_requirements()` - Sampling requirements by system or state
- `get_violations()` - Compliance violations by system or state
- `get_systems()` - List PWSIDs for a state
- `get_state_facilities()` - Get facilities with geocoding data
- `get_state_sampling_points()` - Get sampling points with locations
- `get_facility_geocoding()` - Get geocoding for a specific facility
- `get_sampling_point_geocoding()` - Get geocoding for a sampling point

### Contaminant Helpers

- `get_latest()`, `get_lead()`, `get_pfas()`, `get_coliform()`, `get_nitrate()`
- `get_dbps()`, `get_arsenic()`, `get_manganese()`, `get_vocs()`

### Clients

- `RequirementsClient`, `SystemsClient`, `SamplesClient`

### Agent Class

- `Agent(api_key)` - Initialize Agent Mode client
- `agent.query(prompt, schema=None)` - Natural language query

## Parameters

### `get_results()`

- `pwsid` (str, optional): Public Water System ID
- `address` (str, optional): Address to search near
- `state` (str, optional): State abbreviation (e.g., 'IL', 'CA')
- `analyte` (str, optional): Filter by analyte name (e.g., 'Lead')
- `analyte_group` (str, optional): Filter by group ('pfas', 'metals_inorganic', etc.)
- `api_key` (str, required): Your API key
- `num` (int, optional): Number of results (default: 10, max: 100)
- `latest` (bool, optional): Sort by most recent (default: True)
- `start_date` (str, optional): Filter by start date (ISO format)
- `end_date` (str, optional): Filter by end date (ISO format)
- `radius_miles` (float, optional): Search radius for address queries (default: 10)

## Environment Variables

You can set your API key as an environment variable:

```bash
export MURIEL_API_KEY='your-api-key-here'
```

Then use the SDK without passing the key:

```python
from muriel import get_results

# API key read from environment
results = get_results(pwsid='IL0316000')
```

## Error Handling

```python
from muriel import get_results, MurielAPIError

try:
    results = get_results(
        pwsid='IL0316000',
        api_key='YOUR_API_KEY'
    )
except MurielAPIError as e:
    print(f"API Error: {e.message}")
    print(f"Status Code: {e.status_code}")
```

## Documentation

- Guides and SDK reference: https://docs.murielai.io
- API reference (OpenAPI): https://api.murielai.io/docs

## Support

- Email: info@murielai.io
- Issues: https://github.com/Muriel-AI-Inc/muriel-sdk-python/issues

## License

MIT. Copyright (c) 2024-2026 Muriel AI, Inc. Use of the Muriel API itself is
governed by the terms at https://murielai.io/terms.

# homecastr-python

[![PyPI](https://img.shields.io/pypi/v/homecastr)](https://pypi.org/project/homecastr/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/homecastr)](https://pypi.org/project/homecastr/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Probabilistic home value forecasts for any US address — in one line of Python.**

The Homecastr Python SDK wraps the [Homecastr API](https://www.homecastr.com) and lets you pull property-level, neighborhood-level, and market-level forecasts, run proforma analysis, and build quantitative models on top of the full probability distribution — not just a point estimate.

---

## Table of Contents

- [Data Overview](#data-overview)
- [Getting Started](#getting-started)
- [Services](#services)
  - [Forecast by Address](#forecast-by-address)
  - [Forecast by Neighborhood (H3)](#forecast-by-neighborhood-h3)
  - [Forecast by Parcel](#forecast-by-parcel)
  - [Account & Usage](#account--usage)
- [Cookbook](#cookbook)

---

## Data Overview

Homecastr produces **Bayesian ensemble forecasts** trained on 70M+ US residential transactions. Every forecast returns a full probability distribution (P10/P25/P50/P75/P90) across multiple time horizons — not a single estimate.

| Coverage | Detail |
|---|---|
| **Geography** | Any US street address · H3 hex cells (resolution 8) · County tax parcels |
| **Horizons** | 1–5 year forecasts (12–60 month horizons) |
| **Output** | P10 · P25 · P50 · P75 · P90 probability bands + fan chart |
| **Pro forma** | Cap rate · NOI · DSCR · Monthly rent · Breakeven occupancy |
| **Reliability** | Per-prediction confidence score based on training support and model error |
| **Jurisdictions** | Houston · NYC · SF · Cook County · Seattle · Philadelphia · Florida · Texas · and more |

---

## Getting Started

### Step 1 — Get an API Key

```python
from homecastr import HomecastrClient

# Generate a free API key
client = HomecastrClient()  # uses built-in demo key
result = client.keys.create("you@example.com")
print(result["key"])  # hc_xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

Or sign up at [homecastr.com](https://www.homecastr.com).

### Step 2 — Install

```bash
pip install -U homecastr
```

### Step 3 — Use

```python
import os
from homecastr import HomecastrClient

api_key = os.getenv("HOMECASTR_API_KEY")
client = HomecastrClient(api_key)
```

---

## Services

### Forecast by Address

Get the full probability distribution for any US street address.

```python
# Single address
result = client.forecast.by_address.retrieve(
    "4521 Westheimer Rd Houston TX 77027",
    year=2028,
)

print(result["current_value"])          # 412000
print(result["forecasts"]["p50"])       # 463000  (median forecast)
print(result["forecasts"]["p10"])       # 381000  (downside scenario)
print(result["forecasts"]["p90"])       # 558000  (upside scenario)
print(result["appreciation_pct"])       # 12.4
print(result["reliability"])            # 0.87  (model confidence 0–1)
```

**Bulk retrieval — returns a DataFrame:**

```python
addresses = [
    "4521 Westheimer Rd Houston TX 77027",
    "1234 S Congress Ave Austin TX 78704",
    "567 Valencia St San Francisco CA 94110",
]

df = client.forecast.by_address.retrieve_many(addresses, year=2028)
print(df[["address", "current_value", "p10", "p50", "p90", "appreciation_pct"]])
```

```
                              address  current_value     p10     p50     p90  appreciation_pct
0  4521 Westheimer Rd Houston TX...        412000  381000  463000  558000             12.4
1  1234 S Congress Ave Austin TX...        680000  620000  752000  891000             10.6
2  567 Valencia St San Francisco...       1150000 1040000 1295000 1560000             12.6
```

---

### Forecast by Neighborhood (H3)

Query neighborhood-level metrics using [H3 hex cell IDs](https://h3geo.org/) at resolution 8. Includes proforma underwriting metrics aggregated across all properties in the cell.

```python
# Single hex cell — Midtown Houston
result = client.forecast.by_hex.retrieve("882a100c65fffff", year=2027)

print(result["location"])                       # "Midtown Houston"
print(result["opportunity"])                    # 14.2  (% appreciation)
print(result["reliability"])                    # 0.91
print(result["proforma"]["cap_rate"])           # 0.054
print(result["proforma"]["dscr"])               # 1.21
print(result["proforma"]["monthly_rent"])       # 2350
print(result["bands"]["p50"])                   # 328000
```

**Compare multiple neighborhoods:**

```python
houston_hexes = [
    "882a100c65fffff",  # Midtown
    "882a1008b5fffff",  # Heights
    "882a100d25fffff",  # Montrose
]

df = client.forecast.by_hex.retrieve_many(houston_hexes, year=2027)
print(df[["location", "opportunity", "reliability", "cap_rate", "dscr"]].sort_values("opportunity", ascending=False))
```

---

### Forecast by Parcel

Retrieve lot-level forecasts using county tax parcel account numbers. Returns the full fan chart across all forecast horizons.

```python
# Houston (HCAD) parcel
result = client.forecast.by_parcel.retrieve("0420430060006")

print(result["current_value"])   # 312000
print(result["origin_year"])     # 2025

# Fan chart as a DataFrame
import pandas as pd
df = pd.DataFrame(result["fan_chart"])
print(df[["year", "p10", "p50", "p90"]])
```

```
   year      p10      p50      p90
0  2026   289000   325000   371000
1  2027   295000   342000   396000
2  2028   301000   360000   423000
3  2029   308000   378000   452000
4  2030   315000   397000   483000
```

**Or use the helper:**

```python
df = client.forecast.by_parcel.retrieve_fan_chart("0420430060006")
print(df.attrs["current_value"])  # 312000
```

---

### Account & Usage

Monitor your API usage and quota limits.

```python
info = client.account()

print(info["totals"]["24h"])    # 142
print(info["totals"]["7d"])     # 891
print(info["totals"]["30d"])    # 3204

print(info["by_endpoint"])
# {"/api/v1/forecast": 1840, "/api/v1/forecast/hex": 920, ...}
```

---

## Cookbook

We maintain a [Homecastr Cookbook](https://github.com/homecastr/homecastr-cookbook) with ready-to-run notebooks for common analysis workflows:

- **Getting Started** — API keys, first forecast, data exploration
- **Address Forecasts** — Bulk retrieval, fan chart visualization, uncertainty quantification
- **Neighborhood Analysis** — H3 heat maps, cross-market comparison, opportunity ranking
- **Investment Analysis** — Proforma underwriting, DSCR screening, cap rate distributions
- **Market Comparison** — Houston vs Austin vs SF: 5-year outlook

---

## License

MIT © Homecastr

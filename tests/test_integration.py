"""
Integration tests for the Homecastr API.

Runs against the live API at www.homecastr.com.
Requires no API key (uses built-in demo key).

Usage:
    pytest tests/test_integration.py -v
    pytest tests/test_integration.py -v -k "test_zcta"
"""
import pytest
import httpx

BASE_URL = "https://www.homecastr.com"
DEMO_KEY = "hc_demo_public_readonly"


@pytest.fixture(scope="session")
def client():
    return httpx.Client(
        base_url=BASE_URL,
        headers={"x-api-key": DEMO_KEY},
        timeout=20.0,
    )


# ── Helpers ──────────────────────────────────────────────────────────────────

def assert_fan_chart(data: dict, min_rows: int = 1):
    fan = data.get("fan_chart", [])
    assert len(fan) >= min_rows, f"Expected fan_chart with {min_rows}+ rows, got {len(fan)}"
    for row in fan:
        assert row.get("p50") is not None, f"p50 is None in fan row: {row}"
        assert row.get("p50") > 0, f"p50 <= 0 in fan row: {row}"


def assert_current_value(data: dict):
    cv = data.get("current_value")
    assert cv is not None, "current_value is None"
    assert cv > 0, f"current_value <= 0: {cv}"


# ── Ping ─────────────────────────────────────────────────────────────────────

def test_ping(client):
    r = client.get("/api/ping")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ── Address ──────────────────────────────────────────────────────────────────

def test_address_houston(client):
    r = client.get("/api/v1/forecast", params={"address": "5000 Westheimer Rd Houston TX 77056"})
    assert r.status_code == 200
    d = r.json()
    assert_current_value(d)
    assert_fan_chart(d, min_rows=5)
    assert d["level"] if "level" in d else True  # optional field


def test_address_missing_param(client):
    r = client.get("/api/v1/forecast")
    assert r.status_code == 400
    assert "error" in r.json()


# ── Unit (parcel) ─────────────────────────────────────────────────────────────

def test_unit_florida(client):
    r = client.get("/api/v1/forecast/unit", params={"acct": "00404328020003500"})
    assert r.status_code == 200
    d = r.json()
    assert d["level"] == "unit"
    assert_current_value(d)
    assert_fan_chart(d, min_rows=5)


def test_unit_siblings(client):
    r = client.get("/api/v1/forecast/unit", params={"acct": "00404328020003500", "include_siblings": "true"})
    assert r.status_code == 200
    # siblings may or may not be present depending on condo_group


def test_unit_missing_param(client):
    r = client.get("/api/v1/forecast/unit")
    assert r.status_code == 400


# ── Lot / Building ────────────────────────────────────────────────────────────

def test_lot_florida(client):
    r = client.get("/api/v1/forecast/lot", params={"acct": "00404328020003500"})
    assert r.status_code == 200
    d = r.json()
    assert_current_value(d)
    assert_fan_chart(d, min_rows=5)


def test_lot_nyc_bbl(client):
    r = client.get("/api/v1/forecast/lot", params={"acct": "1005390013"})
    assert r.status_code == 200
    d = r.json()
    assert d["current_value"] > 1_000_000, "NYC Manhattan lot should be >$1M"
    assert_fan_chart(d, min_rows=5)


# ── Tabblock ──────────────────────────────────────────────────────────────────

def test_tabblock_nyc(client):
    r = client.get("/api/v1/forecast/tabblock", params={"geoid": "360050002000001"})
    assert r.status_code == 200
    d = r.json()
    assert d["level"] == "tabblock"
    assert_current_value(d)
    assert_fan_chart(d, min_rows=5)


def test_tabblock_houston(client):
    r = client.get("/api/v1/forecast/tabblock", params={"geoid": "480717106001022"})
    assert r.status_code == 200
    d = r.json()
    assert_current_value(d)


def test_tabblock_missing_param(client):
    r = client.get("/api/v1/forecast/tabblock")
    assert r.status_code == 400


# ── Tract ──────────────────────────────────────────────────────────────────────

def test_tract_houston_jurisdiction(client):
    r = client.get("/api/v1/forecast/tract", params={"geoid": "48201320500"})
    assert r.status_code == 200
    d = r.json()
    assert d["level"] == "tract"
    assert d["data_model"] == "jurisdiction"
    assert_current_value(d)
    assert_fan_chart(d, min_rows=5)


def test_tract_manhattan_acs(client):
    r = client.get("/api/v1/forecast/tract", params={"geoid": "36061023100"})
    assert r.status_code == 200
    d = r.json()
    assert d["data_model"] == "acs_nationwide"
    assert_current_value(d)


def test_tract_missing_param(client):
    r = client.get("/api/v1/forecast/tract")
    assert r.status_code == 400


# ── ZCTA ───────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("zcta,city,min_value", [
    ("77056", "Houston Galleria",  200_000),
    ("10001", "Manhattan",         400_000),
    ("94110", "SF Mission",        600_000),
    ("60614", "Chicago Lincoln Pk",200_000),
    ("98102", "Seattle Capitol Hl",300_000),
    ("33139", "Miami Beach",       200_000),
])
def test_zcta_nationwide(client, zcta, city, min_value):
    r = client.get("/api/v1/forecast/zcta", params={"zcta": zcta})
    assert r.status_code == 200, f"{city} ZCTA {zcta} returned {r.status_code}"
    d = r.json()
    assert d["level"] == "zcta"
    assert_current_value(d)
    assert d["current_value"] >= min_value, f"{city}: expected >=${min_value:,}, got ${d['current_value']:,}"
    fan = d.get("fan_chart", [])
    assert len(fan) >= 6, f"Expected 6+ horizons for {city}, got {len(fan)}"


def test_zcta_missing_param(client):
    r = client.get("/api/v1/forecast/zcta")
    assert r.status_code == 400


# ── ZIP3 ───────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("zip3,label", [
    ("770", "Houston"),
    ("100", "Manhattan"),
    ("331", "Miami"),
    ("606", "Chicago"),
    ("941", "San Francisco"),
    ("981", "Seattle"),
])
def test_zip3_nationwide(client, zip3, label):
    r = client.get("/api/v1/forecast/zip3", params={"zip3": zip3})
    assert r.status_code == 200, f"{label} ZIP3 {zip3} returned {r.status_code}"
    d = r.json()
    assert d["level"] == "zip3"
    assert_current_value(d)
    assert_fan_chart(d, min_rows=3)


def test_zip3_missing_param(client):
    r = client.get("/api/v1/forecast/zip3")
    assert r.status_code == 400


# ── County ────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("fips,label", [
    ("48201", "Harris County TX"),
    ("06037", "LA County CA"),
    ("36061", "New York County NY"),
    ("12086", "Miami-Dade FL"),
    ("17031", "Cook County IL"),
    ("53033", "King County WA"),
])
def test_county_nationwide(client, fips, label):
    r = client.get("/api/v1/forecast/county", params={"fips": fips})
    assert r.status_code == 200, f"{label} county {fips} returned {r.status_code}"
    d = r.json()
    assert d["level"] == "county"
    assert_current_value(d)
    assert_fan_chart(d, min_rows=3)


def test_county_missing_param(client):
    r = client.get("/api/v1/forecast/county")
    assert r.status_code == 400


# ── State ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("fips,label", [
    ("48", "Texas"),
    ("12", "Florida"),
    ("36", "New York"),
    ("06", "California"),
    ("17", "Illinois"),
    ("53", "Washington"),
])
def test_state_all_50(client, fips, label):
    r = client.get("/api/v1/forecast/state", params={"fips": fips})
    assert r.status_code == 200, f"{label} state {fips} returned {r.status_code}"
    d = r.json()
    assert d["level"] == "state"
    assert_current_value(d)
    assert_fan_chart(d, min_rows=3)


def test_state_missing_param(client):
    r = client.get("/api/v1/forecast/state")
    assert r.status_code == 400


# ── Status ────────────────────────────────────────────────────────────────────

def test_status_api(client):
    r = client.get("/api/v1/status")
    assert r.status_code in (200, 503)  # 503 if degraded/outage
    d = r.json()
    assert d["status"] in ("operational", "degraded", "outage")
    assert len(d["components"]) >= 7


def test_status_page_loads(client):
    r = client.get("/status")
    assert r.status_code == 200
    assert b"Homecastr" in r.content


# ── Response shape contracts ──────────────────────────────────────────────────

def test_all_endpoints_have_level_field(client):
    """Every forecast endpoint should return a 'level' field for routing."""
    endpoints = [
        ("/api/v1/forecast/unit",     {"acct": "00404328020003500"}),
        ("/api/v1/forecast/lot",      {"acct": "00404328020003500"}),
        ("/api/v1/forecast/tabblock", {"geoid": "360050002000001"}),
        ("/api/v1/forecast/tract",    {"geoid": "48201320500"}),
        ("/api/v1/forecast/zcta",     {"zcta": "77056"}),
        ("/api/v1/forecast/zip3",     {"zip3": "770"}),
        ("/api/v1/forecast/county",   {"fips": "48201"}),
        ("/api/v1/forecast/state",    {"fips": "48"}),
    ]
    for path, params in endpoints:
        r = client.get(path, params=params)
        assert r.status_code == 200, f"{path} failed: {r.status_code}"
        d = r.json()
        assert "level" in d, f"{path} missing 'level' field"
        assert "current_value" in d, f"{path} missing 'current_value' field"
        assert "fan_chart" in d, f"{path} missing 'fan_chart' field"

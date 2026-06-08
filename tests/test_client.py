"""Basic tests for HomecastrClient."""
import pytest
import httpx
from pytest_httpx import HTTPXMock

from homecastr import HomecastrClient


@pytest.fixture
def client(httpx_mock: HTTPXMock):
    return HomecastrClient("hc_test_key", base_url="https://mock.homecastr.com")


def test_ping(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://mock.homecastr.com/api/ping",
        json={"status": "ok", "service": "homecastr-api", "version": "v1"},
    )
    c = HomecastrClient("hc_test_key", base_url="https://mock.homecastr.com")
    result = c.ping()
    assert result["status"] == "ok"


def test_forecast_by_address(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://mock.homecastr.com/api/v1/forecast?address=123+Main+St+Houston+TX",
        json={
            "address": "123 Main St, Houston, TX 77001",
            "coordinates": {"lat": 29.749907, "lng": -95.358421},
            "current_value": 285000,
            "forecasts": {"p10": 260000, "p50": 310000, "p90": 365000},
            "appreciation_pct": 8.77,
            "reliability": 0.82,
            "forecast_year": 2030,
        },
    )
    c = HomecastrClient("hc_test_key", base_url="https://mock.homecastr.com")
    result = c.forecast.by_address.retrieve("123 Main St Houston TX")
    assert result["current_value"] == 285000
    assert result["forecasts"]["p50"] == 310000


def test_forecast_by_hex(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://mock.homecastr.com/api/v1/forecast/hex?h3_id=882a100c65fffff",
        json={
            "h3_id": "882a100c65fffff",
            "location": "Midtown Houston",
            "opportunity": 12.4,
            "reliability": 0.91,
            "bands": {"p10": 270000, "p50": 320000, "p90": 380000},
            "proforma": {"cap_rate": 0.052, "dscr": 1.18, "monthly_rent": 2200},
        },
    )
    c = HomecastrClient("hc_test_key", base_url="https://mock.homecastr.com")
    result = c.forecast.by_hex.retrieve("882a100c65fffff")
    assert result["proforma"]["cap_rate"] == 0.052


def test_forecast_by_parcel(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://mock.homecastr.com/api/v1/forecast/lot?acct=0420430060006",
        json={
            "acct": "0420430060006",
            "origin_year": 2025,
            "current_value": 312000,
            "fan_chart": [
                {"year": 2026, "horizon_months": 12, "p10": 290000, "p50": 325000, "p90": 370000},
                {"year": 2027, "horizon_months": 24, "p10": 295000, "p50": 340000, "p90": 395000},
            ],
        },
    )
    c = HomecastrClient("hc_test_key", base_url="https://mock.homecastr.com")
    df = c.forecast.by_parcel.retrieve_fan_chart("0420430060006")
    assert len(df) == 2
    assert df.attrs["current_value"] == 312000


def test_keys_create(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://mock.homecastr.com/api/v1/keys",
        method="POST",
        json={"key": "hc_abc123", "email": "test@example.com"},
    )
    c = HomecastrClient("hc_test_key", base_url="https://mock.homecastr.com")
    result = c.keys.create("test@example.com")
    assert result["key"].startswith("hc_")


def test_retrieve_many_returns_dataframe(httpx_mock: HTTPXMock):
    for addr in ["123 Main St Houston TX", "456 Oak Ave Austin TX"]:
        httpx_mock.add_response(
            json={
                "address": addr,
                "coordinates": {"lat": 30.0, "lng": -95.0},
                "current_value": 300000,
                "forecasts": {"p10": 270000, "p50": 310000, "p90": 360000},
                "appreciation_pct": 3.3,
                "reliability": 0.85,
                "forecast_year": 2030,
            }
        )
    c = HomecastrClient("hc_test_key", base_url="https://mock.homecastr.com")
    df = c.forecast.by_address.retrieve_many(
        ["123 Main St Houston TX", "456 Oak Ave Austin TX"]
    )
    assert len(df) == 2
    assert "p50" in df.columns

from __future__ import annotations

from typing import Optional, List

import httpx
import pandas as pd


class _ByAddress:
    """Forecast by US street address."""

    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def retrieve(
        self,
        address: str,
        *,
        year: Optional[int] = None,
    ) -> dict:
        """Get probabilistic home value forecasts for a US street address.

        Parameters
        ----------
        address:
            Full US street address, e.g. ``"4521 Westheimer Rd Houston TX 77027"``.
        year:
            Forecast horizon year (2026–2030). Defaults to 2030.

        Returns
        -------
        dict
            Keys include ``address``, ``coordinates``, ``current_value``,
            ``forecasts`` (p10/p50/p90), ``fan_chart``, and ``reliability``.

        Example
        -------
        >>> result = client.forecast.by_address.retrieve(
        ...     "4521 Westheimer Rd Houston TX 77027",
        ...     year=2028,
        ... )
        >>> print(result["forecasts"]["p50"])
        """
        params: dict = {"address": address}
        if year is not None:
            params["year"] = year

        r = self._http.get("/api/v1/forecast", params=params)
        r.raise_for_status()
        return r.json()

    def retrieve_many(
        self,
        addresses: List[str],
        *,
        year: Optional[int] = None,
    ) -> pd.DataFrame:
        """Retrieve forecasts for multiple addresses and return a DataFrame.

        Parameters
        ----------
        addresses:
            List of US street addresses.
        year:
            Forecast horizon year (2026–2030).

        Returns
        -------
        pandas.DataFrame
            One row per address with columns: ``address``, ``current_value``,
            ``p10``, ``p50``, ``p90``, ``appreciation_pct``, ``reliability``.
        """
        rows = []
        for addr in addresses:
            try:
                data = self.retrieve(addr, year=year)
                rows.append({
                    "address": data.get("address", addr),
                    "lat": data.get("coordinates", {}).get("lat"),
                    "lng": data.get("coordinates", {}).get("lng"),
                    "current_value": data.get("current_value"),
                    "p10": data.get("forecasts", {}).get("p10"),
                    "p50": data.get("forecasts", {}).get("p50"),
                    "p90": data.get("forecasts", {}).get("p90"),
                    "appreciation_pct": data.get("appreciation_pct"),
                    "reliability": data.get("reliability"),
                    "forecast_year": data.get("forecast_year"),
                    "property_count": data.get("property_count"),
                })
            except Exception as exc:
                rows.append({"address": addr, "error": str(exc)})

        return pd.DataFrame(rows)


class _ByHex:
    """Forecast by H3 hexagon cell (resolution 8)."""

    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def retrieve(
        self,
        h3_id: str,
        *,
        year: Optional[int] = None,
    ) -> dict:
        """Get neighborhood-level forecasts for an H3 hex cell.

        Parameters
        ----------
        h3_id:
            H3 cell ID at resolution 8, e.g. ``"882a100c65fffff"``.
        year:
            Forecast horizon year. Defaults to 2026.

        Returns
        -------
        dict
            Keys include ``h3_id``, ``location``, ``coordinates``,
            ``opportunity``, ``reliability``, ``proforma``, ``bands`` (p10/p50/p90),
            and ``scenarios``.

        Example
        -------
        >>> result = client.forecast.by_hex.retrieve("882a100c65fffff")
        >>> print(result["proforma"]["cap_rate"])
        """
        params: dict = {"h3_id": h3_id}
        if year is not None:
            params["year"] = year

        r = self._http.get("/api/v1/forecast/hex", params=params)
        r.raise_for_status()
        return r.json()

    def retrieve_many(
        self,
        h3_ids: List[str],
        *,
        year: Optional[int] = None,
    ) -> pd.DataFrame:
        """Retrieve neighborhood forecasts for multiple H3 cells as a DataFrame.

        Parameters
        ----------
        h3_ids:
            List of H3 cell IDs at resolution 8.
        year:
            Forecast horizon year.

        Returns
        -------
        pandas.DataFrame
            One row per cell with opportunity, reliability, and proforma metrics.
        """
        rows = []
        for h3_id in h3_ids:
            try:
                data = self.retrieve(h3_id, year=year)
                proforma = data.get("proforma", {})
                bands = data.get("bands", {})
                rows.append({
                    "h3_id": data.get("h3_id", h3_id),
                    "location": data.get("location"),
                    "lat": data.get("coordinates", {}).get("lat"),
                    "lng": data.get("coordinates", {}).get("lng"),
                    "opportunity": data.get("opportunity"),
                    "reliability": data.get("reliability"),
                    "p10": bands.get("p10"),
                    "p50": bands.get("p50"),
                    "p90": bands.get("p90"),
                    "predicted_value": proforma.get("predicted_value"),
                    "monthly_rent": proforma.get("monthly_rent"),
                    "cap_rate": proforma.get("cap_rate"),
                    "dscr": proforma.get("dscr"),
                    "noi": proforma.get("noi"),
                    "forecast_year": data.get("forecast_year"),
                })
            except Exception as exc:
                rows.append({"h3_id": h3_id, "error": str(exc)})

        return pd.DataFrame(rows)


class _ByParcel:
    """Forecast by county tax parcel account number."""

    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def retrieve(self, acct: str) -> dict:
        """Get lot-level forecasts for a county tax parcel.

        Parameters
        ----------
        acct:
            County tax parcel account number. Format varies by jurisdiction:
            10-digit for HCAD Houston (e.g. ``"0420430060006"``),
            dash-separated for Florida (e.g. ``"01-4234-001-0010"``).

        Returns
        -------
        dict
            Keys include ``acct``, ``origin_year``, ``current_value``,
            and ``fan_chart`` (array of {year, horizon_months, p10, p25, p50, p75, p90}).

        Example
        -------
        >>> result = client.forecast.by_parcel.retrieve("0420430060006")
        >>> df = pd.DataFrame(result["fan_chart"])
        """
        r = self._http.get("/api/v1/forecast/lot", params={"acct": acct})
        r.raise_for_status()
        return r.json()

    def retrieve_fan_chart(self, acct: str) -> pd.DataFrame:
        """Retrieve the full probability fan chart for a parcel as a DataFrame.

        Parameters
        ----------
        acct:
            County tax parcel account number.

        Returns
        -------
        pandas.DataFrame
            Columns: ``year``, ``horizon_months``, ``p10``, ``p25``, ``p50``,
            ``p75``, ``p90``.
        """
        data = self.retrieve(acct)
        fan = data.get("fan_chart", [])
        df = pd.DataFrame(fan)
        df.attrs["acct"] = data.get("acct", acct)
        df.attrs["current_value"] = data.get("current_value")
        df.attrs["origin_year"] = data.get("origin_year")
        return df


class ForecastService:
    """Access all Homecastr forecast endpoints.

    Attributes
    ----------
    by_address:
        Forecasts by US street address.
    by_hex:
        Neighborhood-level forecasts by H3 hex cell ID.
    by_parcel:
        Lot-level forecasts by county tax parcel account number.
    """

    def __init__(self, http: httpx.Client) -> None:
        self.by_address = _ByAddress(http)
        self.by_hex = _ByHex(http)
        self.by_parcel = _ByParcel(http)

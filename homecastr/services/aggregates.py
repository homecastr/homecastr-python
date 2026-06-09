from __future__ import annotations

from typing import Optional, List

import httpx
import pandas as pd


class _ByUnit:
    """Forecast by individual assessor unit (finest resolution).

    Queries ``metrics_parcel_forecast`` — covers individual condo units,
    SFRs, and townhouses by their assessor account number.
    ``condo_group`` links sibling units within the same building.

    Coverage: Florida statewide, Houston metro (HCAD).
    """

    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def retrieve(self, acct: str, *, include_siblings: bool = False) -> dict:
        """Get unit-level forecasts for an individual assessor parcel.

        Parameters
        ----------
        acct:
            Assessor account number.
            Florida DOR: ``"00404328020003500"``
            Houston HCAD: ``"0420430060006"``
        include_siblings:
            If True and the unit is part of a condo building, also returns
            all sibling units sharing the same ``condo_group``.

        Returns
        -------
        dict
            Keys: ``acct``, ``level``, ``current_value``, ``condo_group``,
            ``fan_chart``, and optionally ``siblings``.
        """
        params: dict = {"acct": acct}
        if include_siblings:
            params["include_siblings"] = "true"
        r = self._http.get("/api/v1/forecast/unit", params=params)
        r.raise_for_status()
        return r.json()

    def retrieve_many(self, accts: List[str]) -> pd.DataFrame:
        rows = []
        for acct in accts:
            try:
                d = self.retrieve(acct)
                fan = d.get("fan_chart", [])
                h12 = next((f for f in fan if (f.get("horizon_months") or 0) == 12), fan[1] if len(fan) > 1 else {})
                rows.append({
                    "acct": d.get("acct", acct),
                    "jurisdiction": d.get("jurisdiction"),
                    "condo_group": d.get("condo_group"),
                    "current_value": d.get("current_value"),
                    "p50_12m": h12.get("p50"),
                    "growth_pct_12m": h12.get("growth_pct"),
                    "is_outlier": d.get("is_outlier"),
                })
            except Exception as exc:
                rows.append({"acct": acct, "error": str(exc)})
        return pd.DataFrame(rows)


class _ByCounty:
    """Forecast by US county (5-digit FIPS). Nationwide coverage."""

    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def retrieve(self, fips: str) -> dict:
        """Get county-level forecasts by 5-digit FIPS code.

        Parameters
        ----------
        fips:
            5-digit county FIPS (state 2 + county 3).
            ``"48201"`` = Harris County TX (Houston)
            ``"06037"`` = Los Angeles County CA
            ``"36061"`` = New York County NY (Manhattan)
            ``"12086"`` = Miami-Dade County FL

        Example
        -------
        >>> result = client.forecast.by_county.retrieve("48201")
        >>> print(result["current_value"])
        """
        r = self._http.get("/api/v1/forecast/county", params={"fips": fips})
        r.raise_for_status()
        return r.json()

    def retrieve_many(self, fips_list: List[str]) -> pd.DataFrame:
        rows = []
        for fips in fips_list:
            try:
                d = self.retrieve(fips)
                fan = {f["horizon_months"]: f for f in d.get("fan_chart", [])}
                h12 = fan.get(12, {})
                h60 = fan.get(60, {})
                rows.append({
                    "fips": d.get("fips", fips),
                    "current_value": d.get("current_value"),
                    "p50_12m": h12.get("p50"),
                    "p50_60m": h60.get("p50"),
                    "growth_pct_12m": h12.get("growth_pct"),
                    "growth_dollar_12m": h12.get("growth_dollar"),
                })
            except Exception as exc:
                rows.append({"fips": fips, "error": str(exc)})
        return pd.DataFrame(rows)


class _ByState:
    """Forecast by US state (2-digit FIPS). All 50 states."""

    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def retrieve(self, fips: str) -> dict:
        """Get state-level forecasts by 2-digit FIPS code.

        Parameters
        ----------
        fips:
            2-digit state FIPS.
            ``"48"`` = Texas  ``"12"`` = Florida  ``"36"`` = New York
            ``"06"`` = California  ``"17"`` = Illinois  ``"53"`` = Washington

        Example
        -------
        >>> result = client.forecast.by_state.retrieve("48")
        >>> result = client.forecast.by_state.retrieve("06")
        """
        r = self._http.get("/api/v1/forecast/state", params={"fips": fips})
        r.raise_for_status()
        return r.json()

    def retrieve_all(self) -> pd.DataFrame:
        """Retrieve forecasts for all 50 states as a DataFrame."""
        STATE_FIPS = [
            "01","02","04","05","06","08","09","10","11","12",
            "13","15","16","17","18","19","20","21","22","23",
            "24","25","26","27","28","29","30","31","32","33",
            "34","35","36","37","38","39","40","41","42","44",
            "45","46","47","48","49","50","51","53","54","55","56",
        ]
        rows = []
        for fips in STATE_FIPS:
            try:
                d = self.retrieve(fips)
                fan = {f["horizon_months"]: f for f in d.get("fan_chart", [])}
                h12 = fan.get(12, {})
                h60 = fan.get(60, {})
                rows.append({
                    "fips": d.get("fips", fips),
                    "current_value": d.get("current_value"),
                    "p50_12m": h12.get("p50"),
                    "p50_60m": h60.get("p50"),
                })
            except Exception as exc:
                rows.append({"fips": fips, "error": str(exc)})
        return pd.DataFrame(rows)


class _ByZip3:
    """Forecast by ZIP3 (first 3 digits of ZIP). Nationwide, 6,210 areas."""

    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def retrieve(self, zip3: str) -> dict:
        """Get ZIP3-level forecasts.

        ZIP3 is the postal sectional center facility area —
        a useful mid-size geography between ZCTA and county.

        Parameters
        ----------
        zip3:
            First 3 digits of a US ZIP code.
            ``"770"`` = Houston  ``"100"`` = Manhattan  ``"331"`` = Miami
            ``"606"`` = Chicago  ``"941"`` = San Francisco  ``"981"`` = Seattle

        Example
        -------
        >>> result = client.forecast.by_zip3.retrieve("770")
        >>> result = client.forecast.by_zip3.retrieve("100")
        """
        r = self._http.get("/api/v1/forecast/zip3", params={"zip3": zip3})
        r.raise_for_status()
        return r.json()

    def retrieve_many(self, zip3_list: List[str]) -> pd.DataFrame:
        rows = []
        for z3 in zip3_list:
            try:
                d = self.retrieve(z3)
                fan = {f["horizon_months"]: f for f in d.get("fan_chart", [])}
                h12 = fan.get(12, {})
                h60 = fan.get(60, {})
                rows.append({
                    "zip3": d.get("zip3", z3),
                    "current_value": d.get("current_value"),
                    "p50_12m": h12.get("p50"),
                    "p50_60m": h60.get("p50"),
                    "growth_pct_12m": h12.get("growth_pct"),
                })
            except Exception as exc:
                rows.append({"zip3": z3, "error": str(exc)})
        return pd.DataFrame(rows)

from __future__ import annotations

from typing import Optional, List

import httpx
import pandas as pd


class _ByTract:
    """Forecast by US Census tract GEOID20 (11 digits)."""

    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def retrieve(self, geoid: str) -> dict:
        """Get probabilistic forecasts for a census tract.

        Parameters
        ----------
        geoid:
            11-digit Census GEOID20, e.g. ``"48201231400"``
            (state 2 + county 3 + tract 6).

        Coverage
        --------
        - Florida statewide + Houston: jurisdiction-specific model (v2_2025)
        - All US tracts (~82K): ACS nationwide model (v2_2024, fallback)

        Returns
        -------
        dict
            Keys: ``geoid``, ``level``, ``jurisdiction``, ``data_model``,
            ``current_value``, ``growth_pct``, ``fan_chart``.

        Example
        -------
        >>> result = client.forecast.by_tract.retrieve("48201231400")
        >>> df = pd.DataFrame(result["fan_chart"])
        """
        r = self._http.get("/api/v1/forecast/tract", params={"geoid": geoid})
        r.raise_for_status()
        return r.json()

    def retrieve_many(self, geoids: List[str]) -> pd.DataFrame:
        """Retrieve tract forecasts for a list of GEOIDs as a DataFrame.

        Parameters
        ----------
        geoids:
            List of 11-digit Census GEOID20 strings.

        Returns
        -------
        pandas.DataFrame
            One row per tract with current_value, growth_pct, p10/p50/p90
            at the first available forecast horizon.
        """
        rows = []
        for geoid in geoids:
            try:
                data = self.retrieve(geoid)
                fan = data.get("fan_chart", [])
                forecast_row = next((f for f in fan if (f.get("horizon_months") or 0) > 0), fan[0] if fan else {})
                rows.append({
                    "geoid": data.get("geoid", geoid),
                    "jurisdiction": data.get("jurisdiction"),
                    "data_model": data.get("data_model"),
                    "current_value": data.get("current_value"),
                    "growth_pct": data.get("growth_pct"),
                    "p10": forecast_row.get("p10"),
                    "p50": forecast_row.get("p50"),
                    "p90": forecast_row.get("p90"),
                    "forecast_year": forecast_row.get("year"),
                })
            except Exception as exc:
                rows.append({"geoid": geoid, "error": str(exc)})
        return pd.DataFrame(rows)


class _ByTabblock:
    """Forecast by US Census tabulation block GEOID20 (15 digits).

    Coverage: NYC (32K tabblocks) and Houston metro (34K tabblocks).
    """

    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def retrieve(self, geoid: str) -> dict:
        """Get probabilistic forecasts for a census tabulation block.

        Parameters
        ----------
        geoid:
            15-digit Census GEOID20, e.g. ``"360050002000001"``
            (state 2 + county 3 + tract 6 + block 4).

        Returns
        -------
        dict
            Keys: ``geoid``, ``level``, ``jurisdiction``,
            ``current_value``, ``growth_pct``, ``growth_dollar``,
            ``fan_chart`` (with growth_pct/growth_dollar per horizon).

        Example
        -------
        >>> # Manhattan (NYC)
        >>> result = client.forecast.by_tabblock.retrieve("360050002000001")
        >>> # Houston (HCAD)
        >>> result = client.forecast.by_tabblock.retrieve("480717106001022")
        """
        r = self._http.get("/api/v1/forecast/tabblock", params={"geoid": geoid})
        r.raise_for_status()
        return r.json()

    def retrieve_many(self, geoids: List[str]) -> pd.DataFrame:
        """Retrieve tabblock forecasts for a list of GEOIDs as a DataFrame.

        Parameters
        ----------
        geoids:
            List of 15-digit Census GEOID20 strings.

        Returns
        -------
        pandas.DataFrame
            One row per tabblock with current_value, growth_pct, p10/p50/p90.
        """
        rows = []
        for geoid in geoids:
            try:
                data = self.retrieve(geoid)
                fan = data.get("fan_chart", [])
                forecast_row = next((f for f in fan if (f.get("horizon_months") or 0) > 0), fan[0] if fan else {})
                rows.append({
                    "geoid": data.get("geoid", geoid),
                    "jurisdiction": data.get("jurisdiction"),
                    "current_value": data.get("current_value"),
                    "growth_pct": data.get("growth_pct"),
                    "growth_dollar": data.get("growth_dollar"),
                    "p10": forecast_row.get("p10"),
                    "p50": forecast_row.get("p50"),
                    "p90": forecast_row.get("p90"),
                    "forecast_year": forecast_row.get("year"),
                })
            except Exception as exc:
                rows.append({"geoid": geoid, "error": str(exc)})
        return pd.DataFrame(rows)


class _ByZcta:
    """Forecast by ZIP Code Tabulation Area (5-digit ZCTA).

    Coverage: ~20,259 ZCTAs nationwide via ACS model (6-year horizon).
    """

    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def retrieve(self, zcta: str) -> dict:
        """Get probabilistic forecasts for a ZIP Code Tabulation Area.

        Parameters
        ----------
        zcta:
            5-digit ZCTA / ZIP code, e.g. ``"77056"`` (Houston Galleria area).

        Returns
        -------
        dict
            Keys: ``zcta``, ``level``, ``jurisdiction``,
            ``current_value``, ``fan_chart`` (0–72 month horizons).

        Example
        -------
        >>> result = client.forecast.by_zcta.retrieve("77056")
        >>> result = client.forecast.by_zcta.retrieve("10001")  # Manhattan
        >>> result = client.forecast.by_zcta.retrieve("94110")  # SF Mission
        """
        r = self._http.get("/api/v1/forecast/zcta", params={"zcta": zcta})
        r.raise_for_status()
        return r.json()

    def retrieve_many(self, zctas: List[str]) -> pd.DataFrame:
        """Retrieve ZCTA forecasts for a list of ZIP codes as a DataFrame.

        Parameters
        ----------
        zctas:
            List of 5-digit ZCTA / ZIP codes.

        Returns
        -------
        pandas.DataFrame
            One row per ZCTA with current_value, p10/p50/p90 at 12-month
            and 60-month horizons.
        """
        rows = []
        for zcta in zctas:
            try:
                data = self.retrieve(zcta)
                fan = {f["horizon_months"]: f for f in data.get("fan_chart", [])}
                h12 = fan.get(12, fan.get(list(fan.keys())[1] if len(fan) > 1 else 0, {}))
                h60 = fan.get(60, {})
                rows.append({
                    "zcta": data.get("zcta", zcta),
                    "jurisdiction": data.get("jurisdiction"),
                    "current_value": data.get("current_value"),
                    "p10_12m": h12.get("p10"),
                    "p50_12m": h12.get("p50"),
                    "p90_12m": h12.get("p90"),
                    "p50_60m": h60.get("p50"),
                    "year_12m": h12.get("year"),
                    "year_60m": h60.get("year"),
                })
            except Exception as exc:
                rows.append({"zcta": zcta, "error": str(exc)})
        return pd.DataFrame(rows)

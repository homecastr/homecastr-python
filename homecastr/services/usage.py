from __future__ import annotations

import httpx


class UsageService:
    """Monitor API usage and quota limits."""

    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def retrieve(self) -> dict:
        """Return API usage statistics for the authenticated key.

        Returns
        -------
        dict
            Keys include ``totals`` ({24h, 7d, 30d} request counts),
            ``by_endpoint``, ``by_source``, and ``by_status``.

        Example
        -------
        >>> info = client.account()
        >>> print(info["totals"]["30d"])
        """
        r = self._http.get("/api/v1/usage")
        r.raise_for_status()
        return r.json()

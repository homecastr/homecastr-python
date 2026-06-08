from __future__ import annotations

import os
from typing import Optional

import httpx

from .services.forecast import ForecastService
from .services.usage import UsageService
from .services.keys import KeysService

_DEFAULT_BASE_URL = "https://www.homecastr.com"
_DEFAULT_TIMEOUT = 30.0


class HomecastrClient:
    """Entry point for the Homecastr API.

    Parameters
    ----------
    api_key:
        Your Homecastr API key (``hc_...``). Defaults to the
        ``HOMECASTR_API_KEY`` environment variable.
    base_url:
        Override the default API base URL.
    timeout:
        HTTP request timeout in seconds (default 30).

    Example
    -------
    >>> import os
    >>> from homecastr import HomecastrClient
    >>> client = HomecastrClient(os.getenv("HOMECASTR_API_KEY"))
    >>> result = client.forecast.by_address.retrieve("123 Main St Houston TX")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        self._api_key = api_key or os.environ.get("HOMECASTR_API_KEY", "hc_demo_public_readonly")
        self._base_url = base_url.rstrip("/")
        self._http = httpx.Client(
            base_url=self._base_url,
            headers={
                "x-api-key": self._api_key,
                "x-homecastr-channel": "sdk",
                "User-Agent": f"homecastr-python/{_sdk_version()}",
            },
            timeout=timeout,
        )

        self.forecast = ForecastService(self._http)
        self.usage = UsageService(self._http)
        self.keys = KeysService(self._http)

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def account(self) -> dict:
        """Return API usage statistics for the authenticated key."""
        return self.usage.retrieve()

    def ping(self) -> dict:
        """Health-check the Homecastr API."""
        r = self._http.get("/api/ping")
        r.raise_for_status()
        return r.json()

    def __repr__(self) -> str:
        masked = f"{self._api_key[:8]}{'*' * max(0, len(self._api_key) - 8)}"
        return f"HomecastrClient(api_key='{masked}', base_url='{self._base_url}')"


def _sdk_version() -> str:
    try:
        from importlib.metadata import version
        return version("homecastr")
    except Exception:
        return "0.1.0"

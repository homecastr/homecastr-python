from __future__ import annotations

from typing import Optional

import httpx


class KeysService:
    """Generate and manage Homecastr API keys."""

    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    def create(self, email: str, *, attribution: Optional[dict] = None) -> dict:
        """Generate a new API key.

        Parameters
        ----------
        email:
            Your email address. One key per email address.
        attribution:
            Optional UTM attribution dict: {source, medium, campaign, content,
            term, landing_url, referrer}.

        Returns
        -------
        dict
            ``{"key": "hc_...", "email": "you@example.com"}``

        Example
        -------
        >>> result = client.keys.create("you@example.com")
        >>> print(result["key"])
        """
        body: dict = {"email": email}
        if attribution:
            body["attribution"] = attribution

        r = self._http.post("/api/v1/keys", json=body)
        r.raise_for_status()
        return r.json()

from __future__ import annotations

import json
import unittest
from datetime import date
from http import HTTPStatus
from typing import Any, Dict, List
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_BASE = "https://www.digea.gr/el/api/epg"
HEADERS = {
    # Use a reasonable User-Agent to mimic a browser and avoid blocks.
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


class DigeaApiSmokeTests(unittest.TestCase):
    """Basic connectivity checks against the public Digea EPG API."""

    @staticmethod
    def _fetch_json(path: str) -> List[Dict[str, Any]]:
        """Retrieve a JSON payload from the Digea API."""
        req = Request(f"{API_BASE}/{path}", headers=HEADERS)
        with urlopen(req, timeout=30) as resp:  # noqa: S310
            if resp.status != HTTPStatus.OK:
                raise AssertionError(
                    f"Unexpected status {resp.status} for {path}"
                )
            payload = json.loads(resp.read().decode("utf-8"))
        if not isinstance(payload, list):
            raise AssertionError(f"Expected list response for {path}")
        return payload

    def test_perioxes_and_channels_available(self) -> None:
        """Ensure perioxes and channels endpoints respond with non-empty lists."""
        try:
            perioxes = self._fetch_json("get-perioxes")
            channels = self._fetch_json("get-channels")
        except (HTTPError, URLError) as exc:  # pragma: no cover - network flaky
            raise AssertionError(f"Network request failed: {exc}") from exc

        assert perioxes, "Expected at least one region from get-perioxes"
        assert channels, "Expected at least one channel from get-channels"

    def test_events_endpoint_accessible(self) -> None:
        """
        Verify the events endpoint responds for today's date.

        The response can legitimately be empty depending on the broadcast
        schedule, so we only assert that it is reachable and returns JSON.
        """
        today = date.today().isoformat()
        try:
            events = self._fetch_json(f"get-events?date={today}")
        except (HTTPError, URLError) as exc:  # pragma: no cover - network flaky
            raise AssertionError(f"Network request failed: {exc}") from exc

        assert isinstance(events, list)

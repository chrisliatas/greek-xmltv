from __future__ import annotations

import json
import unittest
from datetime import date
from http import HTTPStatus
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
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
    def _fetch_json(
        path: str,
        *,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve a JSON payload from the Digea API."""
        req_data = None
        headers = dict(HEADERS)
        if data is not None:
            req_data = urlencode(data).encode("utf-8")
            headers.setdefault(
                "Content-Type", "application/x-www-form-urlencoded; charset=UTF-8"
            )
        req = Request(f"{API_BASE}/{path}", headers=headers, data=req_data, method=method)
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
            perioxes = self._fetch_json(
                "get-perioxes",
                method="POST",
                data={"action": "get_perioxes", "lang": "el"},
            )
            channels = self._fetch_json(
                "get-channels",
                method="POST",
                data={"action": "get_chanels", "lang": "el"},
            )
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
        today = date.today()
        today_str = f"{today.year}-{today.month}-{today.day}"
        try:
            events = self._fetch_json(
                "get-events",
                method="POST",
                data={"action": "get_events", "date": today_str},
            )
        except (HTTPError, URLError) as exc:  # pragma: no cover - network flaky
            raise AssertionError(f"Network request failed: {exc}") from exc

        assert isinstance(events, list)

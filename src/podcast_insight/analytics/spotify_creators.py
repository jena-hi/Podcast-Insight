"""Spotify for Creators — UNOFFICIAL analytics connector.

⚠️  Read this before relying on it:
  * Spotify has NO public API for creator analytics. This reuses your logged-in
    browser session (the `sp_dc` cookie) to call Spotify's own internal endpoints.
  * It is undocumented and unsupported. Spotify can change it at any time, and
    when they do, it will break and need re-inspecting.
  * It is a gray area vs. Spotify's Terms of Service. You accepted this trade-off.

Design — "capture and replay":
  Rather than hard-code fragile endpoints, you capture ONE real analytics request
  from your dashboard's Network tab and paste its URL into .env. The tool replays
  that request with a fresh token each month. When Spotify changes things, you
  re-capture the URL. This is the most resilient way to do unofficial scraping.

Setup (see docs/CONNECTING_ANALYTICS.md for screenshots-level detail):
  SPOTIFY_DC_COOKIE                 your `sp_dc` cookie value (lasts ~1 year)
  SPOTIFY_CREATORS_ANALYTICS_URL    a captured analytics request URL; may contain
                                    {episode_id} and/or {show_id} placeholders
  SPOTIFY_CREATORS_METRIC_KEYS      optional: comma-separated JSON keys to read as
                                    'listens' (default tries common names)
"""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

from .. import config
from ..models import AnalyticsRecord, Episode
from .base import NotConfigured, http_get_json

TOKEN_URL = "https://open.spotify.com/get_access_token?reason=transport&productType=web_player"
# JSON keys we'll treat as the "plays/listens" metric if not explicitly configured.
DEFAULT_LISTEN_KEYS = ["starts", "streams", "plays", "listens", "totalStreams", "count"]


class SpotifyCreatorsConnector:
    name = "spotify"

    def __init__(self) -> None:
        self.sp_dc = config.env("SPOTIFY_DC_COOKIE")
        self.analytics_url = config.env("SPOTIFY_CREATORS_ANALYTICS_URL")
        self.show_id = config.env("SPOTIFY_SHOW_ID")
        keys = config.env("SPOTIFY_CREATORS_METRIC_KEYS")
        self.metric_keys = [k.strip() for k in keys.split(",")] if keys else DEFAULT_LISTEN_KEYS

    def _access_token(self) -> str:
        """Exchange the sp_dc cookie for a short-lived bearer token."""
        data = http_get_json(
            TOKEN_URL,
            headers={
                "Cookie": f"sp_dc={self.sp_dc}",
                "User-Agent": "Mozilla/5.0",
                "App-Platform": "WebPlayer",
            },
        )
        token = data.get("accessToken")
        if not token:
            raise NotConfigured(
                "Couldn't get a Spotify token from the sp_dc cookie. It may have "
                "expired — log into Spotify and re-copy `sp_dc` into .env."
            )
        return token

    def fetch(self, episode: Episode) -> Optional[AnalyticsRecord]:
        if not self.sp_dc:
            raise NotConfigured(
                "Set SPOTIFY_DC_COOKIE in .env (see docs/CONNECTING_ANALYTICS.md)."
            )
        if not self.analytics_url:
            raise NotConfigured(
                "Set SPOTIFY_CREATORS_ANALYTICS_URL — capture one analytics request "
                "from your dashboard's Network tab (see docs/CONNECTING_ANALYTICS.md)."
            )

        url = self.analytics_url.format(
            episode_id=episode.spotify_episode_id or "",
            show_id=self.show_id or "",
        )
        token = self._access_token()
        payload = http_get_json(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Cookie": f"sp_dc={self.sp_dc}",
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json",
            },
        )

        listens = _first_number(payload, self.metric_keys)
        record = AnalyticsRecord(
            platform=self.name,
            pulled_on=date.today(),
            listens=int(listens) if listens is not None else None,
            extra=_collect_numbers(payload),
        )
        return record


def _first_number(obj: Any, keys: list[str]) -> Optional[float]:
    """Depth-first search for the first numeric value under one of `keys`."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in keys and isinstance(v, (int, float)):
                return float(v)
        for v in obj.values():
            found = _first_number(v, keys)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = _first_number(item, keys)
            if found is not None:
                return found
    return None


def _collect_numbers(obj: Any, prefix: str = "", out: Optional[dict] = None) -> dict[str, float]:
    """Flatten top-level numeric fields into extra{} for visibility/debugging."""
    out = out if out is not None else {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}{k}"
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                out[key] = float(v)
            elif isinstance(v, (dict, list)) and len(out) < 25:
                _collect_numbers(v, f"{key}.", out)
    return out

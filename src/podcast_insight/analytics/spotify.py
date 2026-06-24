"""Spotify connector.

What's available where:
  * PUBLIC Web API (this file): episode metadata, and — for the show owner with
    the right scope — some figures. Uses client-credentials auth (CLIENT_ID +
    CLIENT_SECRET). Implemented: confirms the episode and pulls public metadata.
  * DEEP podcast analytics (streams, listeners, retention, follows): these live
    in the **Spotify for Creators** dashboard and are not in the open Web API
    today. The reliable path is the dashboard's CSV export — see the Apple
    connector for the same pattern, and docs/CONNECTING_ANALYTICS.md for details.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from .. import config
from ..models import AnalyticsRecord, Episode
from .base import NotConfigured, http_get_json, http_post_form


class SpotifyConnector:
    name = "spotify"

    def __init__(self) -> None:
        self.client_id = config.env("SPOTIFY_CLIENT_ID")
        self.client_secret = config.env("SPOTIFY_CLIENT_SECRET")

    def _token(self) -> str:
        import base64

        creds = f"{self.client_id}:{self.client_secret}".encode("utf-8")
        auth = base64.b64encode(creds).decode("utf-8")
        data = http_post_form(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            headers={
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        return data["access_token"]

    def fetch(self, episode: Episode) -> Optional[AnalyticsRecord]:
        if not (self.client_id and self.client_secret):
            raise NotConfigured(
                "Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env "
                "(see docs/CONNECTING_ANALYTICS.md)."
            )
        if not episode.spotify_episode_id:
            raise NotConfigured(
                f"Episode '{episode.slug}' has no spotify_episode_id. Set it with "
                f"`podcast-insight set {episode.slug} --spotify <episode_id>`."
            )

        token = self._token()
        data = http_get_json(
            f"https://api.spotify.com/v1/episodes/{episode.spotify_episode_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        # Public metadata confirms the episode; deep listen metrics require the
        # Creators export (merged in by the CSV importer below when present).
        record = AnalyticsRecord(
            platform=self.name,
            pulled_on=date.today(),
            extra={"duration_ms": float(data.get("duration_ms", 0) or 0)},
        )
        return record

    # ── Deep analytics via Spotify for Creators CSV export ───────────────────
    @staticmethod
    def import_export_csv(path: str) -> dict[str, AnalyticsRecord]:
        """Parse a Spotify for Creators CSV export into records keyed by title.

        STUB with the right shape: Spotify's export columns vary, so map them
        here once you've downloaded one. See docs/CONNECTING_ANALYTICS.md.
        """
        raise NotImplementedError(
            "Spotify CSV import isn't wired up yet — see docs/CONNECTING_ANALYTICS.md "
            "for the column mapping to fill in."
        )

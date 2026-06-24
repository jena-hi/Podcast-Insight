"""YouTube connector.

Two tiers of data:
  * PUBLIC stats (this file): views, likes, comments for a video — needs only a
    simple API key (YOUTUBE_API_KEY) and the video id. Implemented and working.
  * PRIVATE analytics (watch time, average view duration, retention, subscribers
    gained): comes from the YouTube Analytics API, which requires OAuth as the
    channel owner. That flow is documented in docs/CONNECTING_ANALYTICS.md and
    stubbed below — wire it up when you're ready.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from .. import config
from ..models import AnalyticsRecord, Episode
from .base import NotConfigured, http_get_json


class YouTubeConnector:
    name = "youtube"

    def __init__(self) -> None:
        self.api_key = config.env("YOUTUBE_API_KEY")

    def fetch(self, episode: Episode) -> Optional[AnalyticsRecord]:
        if not self.api_key:
            raise NotConfigured(
                "Set YOUTUBE_API_KEY in .env (see docs/CONNECTING_ANALYTICS.md)."
            )
        if not episode.youtube_video_id:
            raise NotConfigured(
                f"Episode '{episode.slug}' has no youtube_video_id. Set it with "
                f"`podcast-insight set {episode.slug} --youtube <video_id>`."
            )

        data = http_get_json(
            "https://www.googleapis.com/youtube/v3/videos",
            params={
                "part": "statistics",
                "id": episode.youtube_video_id,
                "key": self.api_key,
            },
        )
        items = data.get("items", [])
        if not items:
            return None
        stats = items[0].get("statistics", {})

        record = AnalyticsRecord(
            platform=self.name,
            pulled_on=date.today(),
            views=_int(stats.get("viewCount")),
            likes=_int(stats.get("likeCount")),
            comments=_int(stats.get("commentCount")),
        )
        # Enrich with private analytics if/when OAuth is wired up.
        self._maybe_add_private_analytics(episode, record)
        return record

    def _maybe_add_private_analytics(self, episode: Episode, record: AnalyticsRecord) -> None:
        """Fill in watch_time / avg_view_duration / subscribers via OAuth.

        STUB: implement once you've completed the OAuth setup in the docs. The
        YouTube Analytics API call would populate:
            record.watch_time_minutes
            record.avg_view_duration_seconds
            record.subscribers_gained
        Left as a no-op so public stats still work today.
        """
        return None


def _int(value) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

"""Data models for episodes, clips, topics, and analytics.

These are the shapes that flow through the whole pipeline. Each Episode is stored
as one JSON file in data/episodes/. Everything generated (topics, blog, social)
gets attached back onto the Episode so there's a single source of truth per show.
"""

from __future__ import annotations

from datetime import date as date_type
from typing import Optional

from pydantic import BaseModel, Field


class Topic(BaseModel):
    """One of the top topics extracted from an episode."""

    title: str
    summary: str = ""
    key_points: list[str] = Field(default_factory=list)
    # Optional rough timestamp where it's discussed, e.g. "05:02".
    timestamp: Optional[str] = None


class Clip(BaseModel):
    """A highlight clip you cut from the episode (in StreamYard, etc.)."""

    id: str
    title: str
    start: Optional[str] = None       # "13:20"
    end: Optional[str] = None         # "16:40"
    note: str = ""                    # your one-liner on why this clip matters
    transcript_excerpt: str = ""      # optional: the words in the clip
    # Generated social copy keyed by platform, e.g. {"linkedin": "...", ...}.
    social: dict[str, str] = Field(default_factory=dict)


class AnalyticsRecord(BaseModel):
    """A snapshot of performance metrics for an episode on one platform.

    Fields are optional because different platforms expose different things. The
    insights engine works with whatever is present.
    """

    platform: str                     # "youtube" | "spotify" | "apple" | "linkedin"
    pulled_on: date_type
    views: Optional[int] = None
    listens: Optional[int] = None
    watch_time_minutes: Optional[float] = None
    avg_view_duration_seconds: Optional[float] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None
    subscribers_gained: Optional[int] = None
    # Cross-platform / LinkedIn-friendly fields.
    impressions: Optional[int] = None
    engagement_rate: Optional[float] = None   # percent, e.g. 4.2 means 4.2%
    attendees: Optional[int] = None           # LinkedIn event attendees
    new_followers: Optional[int] = None
    # Anything platform-specific that doesn't fit above.
    extra: dict[str, float] = Field(default_factory=dict)

    @property
    def engagement(self) -> int:
        return (self.likes or 0) + (self.comments or 0) + (self.shares or 0)


class Episode(BaseModel):
    """The central record for one podcast episode."""

    slug: str                         # filename-safe id, e.g. "how-ai-changes-sales"
    title: str
    date: Optional[date_type] = None
    transcript: str = ""
    host_notes: str = ""

    # Platform links (used by analytics connectors).
    youtube_video_id: Optional[str] = None
    spotify_episode_id: Optional[str] = None
    apple_episode_title: Optional[str] = None   # Apple matches by title in exports

    # Generated + collected data.
    topics: list[Topic] = Field(default_factory=list)
    blog_markdown: str = ""
    # Social copy promoting the blog itself, keyed by platform.
    blog_promo: dict[str, str] = Field(default_factory=dict)
    clips: list[Clip] = Field(default_factory=list)
    analytics: list[AnalyticsRecord] = Field(default_factory=list)

    def clip_by_id(self, clip_id: str) -> Optional[Clip]:
        return next((c for c in self.clips if c.id == clip_id), None)

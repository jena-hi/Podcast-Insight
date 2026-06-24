"""LinkedIn data models — monthly Page snapshot and per-event analytics."""

from __future__ import annotations

from datetime import date as date_type
from typing import Optional

from pydantic import BaseModel, Field


class LinkedInPageSnapshot(BaseModel):
    """Channel-level metrics for a month (profile or company Page).

    Engagement rate is stored as a percent number (e.g. 4.2 == 4.2%).
    """

    period: str                       # "2026-06"
    pulled_on: date_type
    impressions: Optional[int] = None
    # The headline metric: AVERAGE MONTHLY engagement rate, as a percent (4.2 == 4.2%).
    engagement_rate: Optional[float] = None
    new_followers: Optional[int] = None
    total_followers: Optional[int] = None
    reactions: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None
    posts: Optional[int] = None
    source: str = "connectsafely"
    extra: dict[str, float] = Field(default_factory=dict)


class LinkedInCommenter(BaseModel):
    """A person who commented (PII — kept local only)."""

    name: str
    headline: Optional[str] = None
    profile_url: Optional[str] = None
    comment: Optional[str] = None


class LinkedInEvent(BaseModel):
    """Analytics for one podcast held as a LinkedIn Event.

    `episode_slug` links it to an Episode so its aggregate metrics fold into the
    cross-platform insights. `commenters` is PII and never leaves the local disk.
    """

    name: str
    episode_slug: Optional[str] = None
    event_id: Optional[str] = None        # event url or id
    date: Optional[date_type] = None
    pulled_on: Optional[date_type] = None
    attendees: Optional[int] = None       # people who attended
    registrants: Optional[int] = None     # people who registered
    impressions: Optional[int] = None
    engagement_rate: Optional[float] = None
    reactions: Optional[int] = None
    comments_count: Optional[int] = None
    commenters: list[LinkedInCommenter] = Field(default_factory=list)
    source: str = "connectsafely"
    extra: dict[str, float] = Field(default_factory=dict)

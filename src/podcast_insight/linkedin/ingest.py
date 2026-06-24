"""Take structured LinkedIn data (from ConnectSafely or manual) into the system.

The data shape is plain JSON so it doesn't matter where it came from — Claude
pulling it via the ConnectSafely connector, or you pasting a manual export.

Event ingestion also writes a name-FREE aggregate AnalyticsRecord onto the linked
Episode, so LinkedIn performance folds into the cross-platform insights ranking.
The commenter/attendee NAMES stay only in the local LinkedIn event file.
"""

from __future__ import annotations

from datetime import date

from .. import storage
from ..models import AnalyticsRecord
from . import store
from .models import LinkedInEvent, LinkedInPageSnapshot


def import_page(data: dict) -> LinkedInPageSnapshot:
    """Validate + save a monthly page snapshot. `data` needs at least `period`."""
    data.setdefault("pulled_on", date.today().isoformat())
    snapshot = LinkedInPageSnapshot.model_validate(data)
    store.save_page(snapshot)
    return snapshot


def import_event(data: dict) -> LinkedInEvent:
    """Validate + save an event, and fold its aggregate metrics into the episode."""
    data.setdefault("pulled_on", date.today().isoformat())
    event = LinkedInEvent.model_validate(data)
    store.save_event(event)
    _fold_into_episode(event)
    return event


def _fold_into_episode(event: LinkedInEvent) -> None:
    """Attach a name-free LinkedIn AnalyticsRecord to the linked episode."""
    if not event.episode_slug or not storage.exists(event.episode_slug):
        return
    episode = storage.load(event.episode_slug)
    record = AnalyticsRecord(
        platform="linkedin",
        pulled_on=event.pulled_on or date.today(),
        impressions=event.impressions,
        engagement_rate=event.engagement_rate,
        attendees=event.attendees,
        likes=event.reactions,
        comments=event.comments_count,
    )
    # Replace any prior LinkedIn record so re-imports don't pile up duplicates.
    episode.analytics = [r for r in episode.analytics if r.platform != "linkedin"]
    episode.analytics.append(record)
    storage.save(episode)

"""Persist LinkedIn page snapshots and events to local disk (PII stays local)."""

from __future__ import annotations

from pathlib import Path

from .. import config
from .models import LinkedInEvent, LinkedInPageSnapshot


def _page_dir() -> Path:
    d = config.LINKEDIN_DIR / "page"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _events_dir() -> Path:
    d = config.LINKEDIN_DIR / "events"
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_page(snapshot: LinkedInPageSnapshot) -> Path:
    path = _page_dir() / f"{snapshot.period}.json"
    path.write_text(snapshot.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_page(period: str) -> LinkedInPageSnapshot:
    path = _page_dir() / f"{period}.json"
    if not path.exists():
        raise FileNotFoundError(f"No LinkedIn page snapshot for {period}.")
    return LinkedInPageSnapshot.model_validate_json(path.read_text(encoding="utf-8"))


def all_page_snapshots() -> list[LinkedInPageSnapshot]:
    snaps = []
    for p in _page_dir().glob("*.json"):
        try:
            snaps.append(LinkedInPageSnapshot.model_validate_json(p.read_text(encoding="utf-8")))
        except Exception:  # noqa: BLE001
            continue
    snaps.sort(key=lambda s: s.period)
    return snaps


def _event_key(event: LinkedInEvent) -> str:
    return event.episode_slug or event.event_id or event.name.lower().replace(" ", "-")


def save_event(event: LinkedInEvent) -> Path:
    path = _events_dir() / f"{_event_key(event)}.json"
    path.write_text(event.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_event(key: str) -> LinkedInEvent:
    path = _events_dir() / f"{key}.json"
    if not path.exists():
        raise FileNotFoundError(f"No LinkedIn event '{key}'.")
    return LinkedInEvent.model_validate_json(path.read_text(encoding="utf-8"))


def all_events() -> list[LinkedInEvent]:
    events = []
    for p in _events_dir().glob("*.json"):
        try:
            events.append(LinkedInEvent.model_validate_json(p.read_text(encoding="utf-8")))
        except Exception:  # noqa: BLE001
            continue
    from datetime import date as _date

    events.sort(key=lambda e: e.date or _date.min, reverse=True)
    return events

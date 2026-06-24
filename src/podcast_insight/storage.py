"""Reading and writing episodes to disk.

The "database" is just one JSON file per episode in data/episodes/. Simple, easy
to inspect, easy to back up, and you can edit them by hand if needed.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from . import config
from .models import Episode


def slugify(text: str) -> str:
    """Turn a title into a filename-safe slug, e.g. 'How AI?' -> 'how-ai'."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-") or "episode"


def _path_for(slug: str) -> Path:
    return config.EPISODES_DIR / f"{slug}.json"


def save(episode: Episode) -> Path:
    """Persist an episode to data/episodes/<slug>.json."""
    config.ensure_dirs()
    path = _path_for(episode.slug)
    path.write_text(
        episode.model_dump_json(indent=2, exclude_none=False),
        encoding="utf-8",
    )
    return path


def load(slug: str) -> Episode:
    """Load an episode by slug. Raises FileNotFoundError if it doesn't exist."""
    path = _path_for(slug)
    if not path.exists():
        raise FileNotFoundError(
            f"No episode '{slug}'. Run `podcast-insight list` to see what exists."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    return Episode.model_validate(data)


def exists(slug: str) -> bool:
    return _path_for(slug).exists()


def all_episodes() -> list[Episode]:
    """Load every stored episode, newest first where dates are known."""
    config.ensure_dirs()
    episodes = []
    for path in config.EPISODES_DIR.glob("*.json"):
        try:
            episodes.append(Episode.model_validate_json(path.read_text(encoding="utf-8")))
        except Exception:  # noqa: BLE001 — skip anything malformed, keep going
            continue
    from datetime import date as _date

    episodes.sort(key=lambda e: e.date or _date.min, reverse=True)
    return episodes

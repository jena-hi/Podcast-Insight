"""Load a transcript file into an Episode.

Accepts plain text or markdown. Most transcript sources (StreamYard, YouTube
captions, Descript, Otter) can export one of these. Timestamps like [00:00] or
00:00 are fine — they're kept and can help topic extraction.
"""

from __future__ import annotations

from datetime import date as date_type
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..models import Episode
from ..storage import slugify


def read_transcript(path: str | Path) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Transcript file not found: {p}")
    return p.read_text(encoding="utf-8").strip()


def _parse_date(value: Optional[str]) -> Optional[date_type]:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Couldn't parse date '{value}'. Use YYYY-MM-DD.")


def build_episode(
    transcript_path: str | Path,
    title: str,
    date: Optional[str] = None,
    notes: str = "",
    slug: Optional[str] = None,
) -> Episode:
    """Create an Episode object from a transcript file plus metadata."""
    text = read_transcript(transcript_path)
    return Episode(
        slug=slug or slugify(title),
        title=title,
        date=_parse_date(date),
        transcript=text,
        host_notes=notes,
    )

"""Pull a transcript straight from a YouTube URL — no API key, no paid tools.

Uses:
  * youtube-transcript-api  → the auto-generated (or uploaded) captions
  * YouTube's free oEmbed endpoint → the video title and author

This is what powers `podcast-insight from-youtube <url>`: paste a link, get a
blog + promo caption. Note: YouTube sometimes blocks transcript requests from
cloud/datacenter IPs, so this is most reliable run locally / interactively.
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from typing import Optional

from ..models import Episode
from ..storage import slugify

_YT_ID_PATTERNS = [
    r"(?:v=|/watch\?.*v=)([0-9A-Za-z_-]{11})",
    r"youtu\.be/([0-9A-Za-z_-]{11})",
    r"/live/([0-9A-Za-z_-]{11})",
    r"/shorts/([0-9A-Za-z_-]{11})",
    r"/embed/([0-9A-Za-z_-]{11})",
]


def extract_video_id(url_or_id: str) -> str:
    """Accept a full YouTube URL (any common form) or a bare 11-char id."""
    s = url_or_id.strip()
    if re.fullmatch(r"[0-9A-Za-z_-]{11}", s):
        return s
    for pat in _YT_ID_PATTERNS:
        m = re.search(pat, s)
        if m:
            return m.group(1)
    raise ValueError(f"Couldn't find a YouTube video id in: {url_or_id}")


def fetch_title(video_id: str) -> tuple[Optional[str], Optional[str]]:
    """Return (title, author) via YouTube's free, keyless oEmbed endpoint."""
    url = "https://www.youtube.com/oembed?" + urllib.parse.urlencode(
        {"url": f"https://www.youtube.com/watch?v={video_id}", "format": "json"}
    )
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:  # noqa: S310
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("title"), data.get("author_name")
    except Exception:  # noqa: BLE001 — title is best-effort
        return None, None


def fetch_transcript(video_id: str, languages: list[str] | None = None) -> str:
    """Return the transcript text for a video, newlines between caption lines."""
    languages = languages or ["en", "en-US", "en-GB"]
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("youtube-transcript-api not installed. Run: pip install -e .") from exc

    entries = _get_entries(YouTubeTranscriptApi, video_id, languages)
    lines = []
    for e in entries:
        text = e.get("text") if isinstance(e, dict) else getattr(e, "text", "")
        if text and text.strip():
            lines.append(text.strip())
    if not lines:
        raise RuntimeError(
            f"No transcript found for video {video_id}. The video may have "
            f"captions disabled, or YouTube is blocking this IP (try running locally)."
        )
    return "\n".join(lines)


def _get_entries(api, video_id: str, languages: list[str]):
    """Handle both the old classmethod API and the newer instance API."""
    # Older: YouTubeTranscriptApi.get_transcript(id, languages=...)
    if hasattr(api, "get_transcript"):
        try:
            return api.get_transcript(video_id, languages=languages)
        except Exception:  # noqa: BLE001 — fall back to any available language
            listing = api.list_transcripts(video_id)
            return listing.find_transcript(languages).fetch()
    # Newer: YouTubeTranscriptApi().fetch(id, languages=...) -> FetchedTranscript
    inst = api()
    fetched = inst.fetch(video_id, languages=languages)
    return list(fetched)


def build_episode_from_youtube(
    url_or_id: str,
    title: Optional[str] = None,
    date: Optional[str] = None,
    notes: str = "",
    slug: Optional[str] = None,
    languages: list[str] | None = None,
) -> Episode:
    """Fetch transcript + title from YouTube and build an Episode."""
    from .transcript import _parse_date  # reuse the date parser

    video_id = extract_video_id(url_or_id)
    transcript = fetch_transcript(video_id, languages)
    yt_title, _author = (None, None) if title else fetch_title(video_id)
    final_title = title or yt_title or f"YouTube {video_id}"

    return Episode(
        slug=slug or slugify(final_title),
        title=final_title,
        date=_parse_date(date),
        transcript=transcript,
        host_notes=notes,
        youtube_video_id=video_id,
    )

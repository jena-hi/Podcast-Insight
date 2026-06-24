"""Write generated content to data/output/ in a tidy, findable layout."""

from __future__ import annotations

from pathlib import Path

from . import config
from .models import Episode


def _dir(name: str) -> Path:
    d = config.OUTPUT_DIR / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def write_blog(episode: Episode) -> Path:
    path = _dir("blog") / f"{episode.slug}.md"
    path.write_text(episode.blog_markdown, encoding="utf-8")
    return path


def write_social(episode: Episode) -> Path:
    """Write one markdown file per episode with all clips' copy."""
    path = _dir("social") / f"{episode.slug}.md"
    lines = [f"# Social copy — {episode.title}", ""]
    for clip in episode.clips:
        lines.append(f"## {clip.title}  ({clip.start or '?'}–{clip.end or '?'})")
        if clip.note:
            lines.append(f"_{clip.note}_")
        lines.append("")
        if not clip.social:
            lines.append("_(no copy generated yet)_\n")
            continue
        for platform, copy in clip.social.items():
            lines.append(f"### {platform.capitalize()}")
            lines.append(copy)
            lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_topics(episode: Episode) -> Path:
    path = _dir("topics") / f"{episode.slug}.md"
    lines = [f"# Top topics — {episode.title}", ""]
    for i, t in enumerate(episode.topics, 1):
        ts = f" ({t.timestamp})" if t.timestamp else ""
        lines.append(f"## {i}. {t.title}{ts}")
        if t.summary:
            lines.append(t.summary)
        for kp in t.key_points:
            lines.append(f"- {kp}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_insights(markdown: str) -> Path:
    path = _dir("insights") / "latest.md"
    path.write_text(markdown, encoding="utf-8")
    return path

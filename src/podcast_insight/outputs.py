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


def write_promo(episode: Episode) -> Path:
    """Write the blog-promo caption(s) to a markdown file."""
    path = _dir("promo") / f"{episode.slug}.md"
    lines = [f"# Blog promo caption — {episode.title}", ""]
    if not episode.blog_promo:
        lines.append("_(no promo generated yet)_")
    for platform, copy in episode.blog_promo.items():
        lines.append(f"## {platform.capitalize()}")
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


def write_insights(markdown: str, stamp: str | None = None) -> Path:
    """Write insights to data/output/ and a git-tracked copy in reports/.

    `stamp` (e.g. '2026-06') names the tracked report; pass it from the caller
    since workflow time isn't available inside the library.
    """
    path = _dir("insights") / "latest.md"
    path.write_text(markdown, encoding="utf-8")

    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (config.REPORTS_DIR / "insights-latest.md").write_text(markdown, encoding="utf-8")
    if stamp:
        (config.REPORTS_DIR / f"insights-{stamp}.md").write_text(markdown, encoding="utf-8")
    return path

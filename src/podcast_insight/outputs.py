"""Write generated content to data/output/ in a tidy, findable layout."""

from __future__ import annotations

from pathlib import Path

from . import config
from .models import Episode


def _dir(name: str) -> Path:
    d = config.OUTPUT_DIR / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def _publish(slug: str, filename: str, text: str) -> Path:
    """Write a publishable deliverable to the git-tracked content/<slug>/ folder."""
    d = config.CONTENT_DIR / slug
    d.mkdir(parents=True, exist_ok=True)
    path = d / filename
    path.write_text(text, encoding="utf-8")
    return path


def write_blog(episode: Episode) -> Path:
    """Write the blog. Local working copy + git-tracked content/ copy (returned)."""
    (_dir("blog") / f"{episode.slug}.md").write_text(episode.blog_markdown, encoding="utf-8")
    return _publish(episode.slug, "blog.md", episode.blog_markdown)


def write_social(episode: Episode) -> Path:
    """Write one markdown file per episode with all clips' copy."""
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
    text = "\n".join(lines)
    (_dir("social") / f"{episode.slug}.md").write_text(text, encoding="utf-8")
    return _publish(episode.slug, "social.md", text)


def write_promo(episode: Episode) -> Path:
    """Write the blog-promo caption(s) to a markdown file."""
    lines = [f"# Blog promo caption — {episode.title}", ""]
    if not episode.blog_promo:
        lines.append("_(no promo generated yet)_")
    for platform, copy in episode.blog_promo.items():
        lines.append(f"## {platform.capitalize()}")
        lines.append(copy)
        lines.append("")
    text = "\n".join(lines)
    (_dir("promo") / f"{episode.slug}.md").write_text(text, encoding="utf-8")
    return _publish(episode.slug, "promo.md", text)


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


def write_tiktok(episode: Episode, videos) -> Path:
    """Write each TikTok spec (JSON) + a human-readable summary for the episode."""
    out = _dir("tiktok") / episode.slug
    out.mkdir(parents=True, exist_ok=True)
    lines = [f"# TikTok scripts — {episode.title}", ""]
    for i, v in enumerate(videos, 1):
        (out / f"topic-{i}.json").write_text(v.model_dump_json(indent=2), encoding="utf-8")
        lines.append(f"## {i}. {v.topic_title}  ({v.total_duration}s)")
        lines.append(f"**Hook:** {v.hook}")
        lines.append("")
        lines.append("**Storyboard:**")
        for s in v.scenes:
            lines.append(f"- [{s.start:g}–{s.start + s.duration:g}s] *{s.role}* — "
                         f"{s.on_screen_text}  ({s.visual})")
        lines.append("")
        lines.append(f"**Voiceover:** {v.voiceover_script}")
        if v.voiceover_audio_path:
            lines.append(f"**Voiceover audio:** {v.voiceover_audio_path}")
        lines.append(f"**Music:** {v.music_mood}")
        lines.append("")
        lines.append(f"**Caption:** {v.caption}")
        if v.hashtags:
            lines.append(" ".join(f"#{h.lstrip('#')}" for h in v.hashtags))
        lines.append("")
    text = "\n".join(lines)
    (out / "summary.md").write_text(text, encoding="utf-8")
    return _publish(episode.slug, "tiktok-scripts.md", text)


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

"""Render the two LinkedIn dashboards.

  * Page dashboard (monthly): impressions, engagement rate, new followers, with
    month-over-month deltas. No PII → safe to write to the git-tracked reports/.
  * Event dashboard (per podcast/event): attendees, impressions, engagement rate,
    and the list of people who commented. Contains names → written LOCAL ONLY
    under data/output/ (git-ignored).
"""

from __future__ import annotations

from pathlib import Path

from .. import config
from .models import LinkedInEvent, LinkedInPageSnapshot
from .store import all_page_snapshots


def _fmt(n) -> str:
    if n is None:
        return "—"
    if isinstance(n, float):
        return f"{n:,.1f}"
    return f"{n:,}"


def _delta(curr, prev) -> str:
    if curr is None or prev is None:
        return ""
    diff = curr - prev
    if diff == 0:
        return " (±0)"
    arrow = "▲" if diff > 0 else "▼"
    return f" ({arrow}{_fmt(abs(diff))})"


def render_page_dashboard(snapshot: LinkedInPageSnapshot) -> str:
    """Monthly LinkedIn Page dashboard markdown (no PII)."""
    prev = None
    history = [s for s in all_page_snapshots() if s.period < snapshot.period]
    if history:
        prev = history[-1]

    def row(label, attr, suffix=""):
        curr = getattr(snapshot, attr)
        d = _delta(curr, getattr(prev, attr, None)) if prev else ""
        val = _fmt(curr) + (suffix if curr is not None else "")
        return f"| {label} | {val}{d} |"

    page_name = config.settings().get("linkedin", {}).get("page_name", "")
    heading = f"# LinkedIn — monthly page dashboard ({snapshot.period})"
    if page_name:
        heading = f"# {page_name} — LinkedIn page dashboard ({snapshot.period})"
    lines = [
        heading,
        "",
        f"_Pulled {snapshot.pulled_on} via {snapshot.source}._"
        + (f" Compared to {prev.period}." if prev else ""),
        "",
        "| Metric | Value |",
        "|---|---|",
        row("Avg. monthly engagement rate", "engagement_rate", "%"),
        row("Impressions", "impressions"),
        row("New followers", "new_followers"),
        row("Total followers", "total_followers"),
        row("Reactions", "reactions"),
        row("Comments", "comments"),
        row("Shares", "shares"),
        row("Posts", "posts"),
        "",
    ]
    return "\n".join(lines)


def render_event_dashboard(event: LinkedInEvent) -> str:
    """Per-event dashboard markdown — INCLUDES commenter names (local only)."""
    date_str = event.date.isoformat() if event.date else "?"
    lines = [
        f"# LinkedIn event — {event.name}",
        "",
        f"_Event date: {date_str}"
        + (f" · linked to episode `{event.episode_slug}`" if event.episode_slug else "")
        + (f" · pulled {event.pulled_on}" if event.pulled_on else "")
        + "._",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Attendees | {_fmt(event.attendees)} |",
        f"| Registrants | {_fmt(event.registrants)} |",
        f"| Impressions | {_fmt(event.impressions)} |",
        f"| Engagement rate | {_fmt(event.engagement_rate)}{'%' if event.engagement_rate is not None else ''} |",
        f"| Reactions | {_fmt(event.reactions)} |",
        f"| Comments | {_fmt(event.comments_count)} |",
        "",
        f"## People who commented ({len(event.commenters)})",
        "",
    ]
    if not event.commenters:
        lines.append("_No commenters captured._")
    else:
        for c in event.commenters:
            bits = [f"**{c.name}**"]
            if c.headline:
                bits.append(c.headline)
            line = " — ".join(bits)
            if c.profile_url:
                line += f"  ·  {c.profile_url}"
            lines.append(f"- {line}")
            if c.comment:
                snippet = c.comment.strip().replace("\n", " ")
                if len(snippet) > 200:
                    snippet = snippet[:197] + "..."
                lines.append(f"    > {snippet}")
    lines.append("")
    lines.append("_This file contains personal data and is kept local (git-ignored)._")
    return "\n".join(lines)


# ── output paths ─────────────────────────────────────────────────────────────

def write_page_dashboard(snapshot: LinkedInPageSnapshot) -> Path:
    """Page dashboard → git-tracked reports/ (no PII)."""
    config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = config.REPORTS_DIR / f"linkedin-page-{snapshot.period}.md"
    path.write_text(render_page_dashboard(snapshot), encoding="utf-8")
    # Also keep a "latest" for convenience.
    (config.REPORTS_DIR / "linkedin-page-latest.md").write_text(
        render_page_dashboard(snapshot), encoding="utf-8"
    )
    return path


def write_event_dashboard(event: LinkedInEvent) -> Path:
    """Event dashboard → local only (git-ignored), because it has names."""
    out = config.OUTPUT_DIR / "linkedin"
    out.mkdir(parents=True, exist_ok=True)
    key = event.episode_slug or event.event_id or event.name.lower().replace(" ", "-")
    path = out / f"{key}.md"
    path.write_text(render_event_dashboard(event), encoding="utf-8")
    return path

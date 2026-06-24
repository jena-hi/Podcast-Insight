"""Rank top-performing episodes and generate recommendations.

Scoring approach (deliberately simple and explainable):
  1. For each episode, aggregate metrics across all its platform records.
  2. Min-max normalize each metric across the whole catalog (0..1).
  3. Combine into one score using the weights in config/settings.yaml.
  4. Hand the ranked, human-readable summary to Claude for qualitative analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .. import config
from ..ai import prompts
from ..ai.client import AIClient, GenerationResult
from ..models import Episode

# Which AnalyticsRecord-derived metric each scoring weight maps to.
METRIC_FIELDS = {
    "views": "views",
    "watch_time": "watch_time_minutes",
    "avg_view_duration": "avg_view_duration_seconds",
    "engagement": "engagement",
    "listens": "listens",
    "impressions": "impressions",      # LinkedIn (+ any platform that reports it)
    "attendees": "attendees",          # LinkedIn events
}


@dataclass
class EpisodeScore:
    slug: str
    title: str
    score: float = 0.0
    metrics: dict[str, float] = field(default_factory=dict)


def _aggregate(episode: Episode) -> dict[str, float]:
    """Sum/average the relevant metrics across an episode's platform records."""
    out: dict[str, float] = {}
    for key, field_name in METRIC_FIELDS.items():
        values = []
        for rec in episode.analytics:
            val = getattr(rec, field_name, None)
            if val is not None:
                values.append(float(val))
        if values:
            # Durations are averaged; everything else summed across platforms.
            out[key] = sum(values) / len(values) if "duration" in field_name else sum(values)
    return out


def score_episodes(episodes: list[Episode]) -> list[EpisodeScore]:
    """Return episodes scored and sorted high-to-low."""
    weights = config.settings().get("analytics", {}).get("scoring_weights", {})
    raw = {e.slug: _aggregate(e) for e in episodes}

    # Min-max bounds per metric across the catalog.
    bounds: dict[str, tuple[float, float]] = {}
    for key in METRIC_FIELDS:
        vals = [m[key] for m in raw.values() if key in m]
        if vals:
            bounds[key] = (min(vals), max(vals))

    scores: list[EpisodeScore] = []
    for ep in episodes:
        metrics = raw[ep.slug]
        total = 0.0
        for key, weight in weights.items():
            if key in metrics and key in bounds:
                lo, hi = bounds[key]
                norm = 0.0 if hi == lo else (metrics[key] - lo) / (hi - lo)
                total += weight * norm
        scores.append(EpisodeScore(slug=ep.slug, title=ep.title, score=round(total, 4), metrics=metrics))

    scores.sort(key=lambda s: s.score, reverse=True)
    return scores


def render_summary(episodes: list[Episode], scores: list[EpisodeScore]) -> str:
    """A compact, human/AI-readable table of the scored data."""
    by_slug = {e.slug: e for e in episodes}
    lines = ["Episode performance (ranked by combined score):", ""]
    for rank, s in enumerate(scores, 1):
        ep = by_slug[s.slug]
        date_str = ep.date.isoformat() if ep.date else "?"
        topics = ", ".join(t.title for t in ep.topics) or "(no topics extracted)"
        metric_str = ", ".join(f"{k}={int(v) if v == int(v) else round(v, 1)}" for k, v in s.metrics.items()) or "(no metrics)"
        lines.append(
            f"{rank}. \"{ep.title}\" [{date_str}] score={s.score}\n"
            f"     metrics: {metric_str}\n"
            f"     topics: {topics}\n"
            f"     clips: {len(ep.clips)}"
        )
    return "\n".join(lines)


def generate_insights(
    episodes: list[Episode], client: AIClient | None = None
) -> tuple[str, list[EpisodeScore], GenerationResult]:
    """Score episodes and ask Claude for patterns + recommendations.

    Returns (insights_markdown, scores, raw_result). In dry-run mode the markdown
    is empty and the prompt is written to a file.
    """
    client = client or AIClient()
    if not episodes:
        raise ValueError("No episodes found. Ingest some first.")

    scores = score_episodes(episodes)
    summary = render_summary(episodes, scores)
    system, user = prompts.insights_prompt(summary)
    result = client.generate("insights", system, user, temperature=0.5)

    if result.dry_run:
        return "", scores, result
    return result.text, scores, result

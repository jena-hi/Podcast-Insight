"""Smoke tests that exercise the pipeline in dry-run mode (no API key needed)."""

from __future__ import annotations

import os

# Ensure dry-run: no API key during tests.
os.environ.pop("ANTHROPIC_API_KEY", None)

from podcast_insight.ai._json import parse_json  # noqa: E402
from podcast_insight.analytics.insights import score_episodes  # noqa: E402
from podcast_insight.ingest.transcript import build_episode  # noqa: E402
from podcast_insight.models import AnalyticsRecord, Clip, Episode  # noqa: E402
from podcast_insight.storage import slugify  # noqa: E402


def test_slugify():
    assert slugify("How AI Is Changing Sales!") == "how-ai-is-changing-sales"
    assert slugify("  Multiple   Spaces ") == "multiple-spaces"


def test_parse_json_with_fence():
    assert parse_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_json('Sure! {"a": 2} done') == {"a": 2}


def test_build_episode(tmp_path):
    f = tmp_path / "t.md"
    f.write_text("hello transcript", encoding="utf-8")
    ep = build_episode(str(f), title="Test Ep", date="2026-01-02")
    assert ep.slug == "test-ep"
    assert ep.transcript == "hello transcript"
    assert ep.date.isoformat() == "2026-01-02"


def test_scoring_ranks_higher_metrics_first():
    e1 = Episode(slug="low", title="Low")
    e1.analytics.append(AnalyticsRecord(platform="youtube", pulled_on="2026-01-01", views=10, likes=1))
    e2 = Episode(slug="high", title="High")
    e2.analytics.append(AnalyticsRecord(platform="youtube", pulled_on="2026-01-01", views=1000, likes=200))
    scores = score_episodes([e1, e2])
    assert scores[0].slug == "high"
    assert scores[0].score >= scores[1].score


def test_engagement_property():
    rec = AnalyticsRecord(platform="youtube", pulled_on="2026-01-01", likes=5, comments=3, shares=2)
    assert rec.engagement == 10


def test_clip_lookup():
    ep = Episode(slug="x", title="X", clips=[Clip(id="abc", title="Clip A")])
    assert ep.clip_by_id("abc").title == "Clip A"
    assert ep.clip_by_id("nope") is None

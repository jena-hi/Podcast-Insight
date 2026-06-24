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


def test_youtube_id_extraction():
    from podcast_insight.ingest.youtube import extract_video_id

    cases = {
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ": "dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ?si=abc": "dQw4w9WgXcQ",
        "https://www.youtube.com/live/dQw4w9WgXcQ": "dQw4w9WgXcQ",
        "https://www.youtube.com/shorts/dQw4w9WgXcQ": "dQw4w9WgXcQ",
        "dQw4w9WgXcQ": "dQw4w9WgXcQ",
    }
    for url, expected in cases.items():
        assert extract_video_id(url) == expected


def test_spotify_first_number_search():
    from podcast_insight.analytics.spotify_creators import _first_number

    payload = {"data": {"detailedStreams": {"starts": 1234, "other": "x"}}}
    assert _first_number(payload, ["starts"]) == 1234.0
    assert _first_number(payload, ["nope"]) is None


def test_linkedin_event_dashboard_has_names_and_metrics():
    from podcast_insight.linkedin.models import LinkedInCommenter, LinkedInEvent
    from podcast_insight.linkedin.reports import render_event_dashboard

    event = LinkedInEvent(
        name="Test Event", attendees=120, impressions=5000, engagement_rate=6.1,
        comments_count=2,
        commenters=[
            LinkedInCommenter(name="Jane Doe", comment="Great point."),
            LinkedInCommenter(name="Sam Rivera"),
        ],
    )
    md = render_event_dashboard(event)
    assert "Jane Doe" in md and "Sam Rivera" in md
    assert "120" in md and "5,000" in md
    assert "6.1%" in md
    assert "local" in md.lower()  # PII notice


def test_linkedin_event_folds_into_episode(tmp_path, monkeypatch):
    from podcast_insight import config, storage
    from podcast_insight.linkedin import ingest as li_ingest
    from podcast_insight.models import Episode

    # Isolate all writes to tmp so we don't touch real data dirs.
    monkeypatch.setattr(config, "EPISODES_DIR", tmp_path / "episodes")
    monkeypatch.setattr(config, "LINKEDIN_DIR", tmp_path / "linkedin")
    monkeypatch.setattr(config, "OUTPUT_DIR", tmp_path / "output")

    storage.save(Episode(slug="ep1", title="Ep 1"))
    li_ingest.import_event({
        "name": "Ep 1 Live", "episode_slug": "ep1",
        "attendees": 90, "impressions": 3000, "engagement_rate": 5.0,
        "reactions": 40, "comments_count": 12,
        "commenters": [{"name": "Private Person"}],
    })

    ep = storage.load("ep1")
    li = [r for r in ep.analytics if r.platform == "linkedin"]
    assert len(li) == 1
    assert li[0].attendees == 90 and li[0].impressions == 3000
    assert li[0].engagement == 52  # reactions(40) + comments(12)

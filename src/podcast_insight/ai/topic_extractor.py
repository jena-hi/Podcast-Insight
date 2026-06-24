"""Extract and rank the top N topics from an episode transcript."""

from __future__ import annotations

from .. import config
from ..models import Episode, Topic
from . import prompts
from ._json import parse_json
from .client import AIClient, GenerationResult


def extract_topics(episode: Episode, client: AIClient | None = None) -> tuple[list[Topic], GenerationResult]:
    """Return the top topics for an episode (and the raw generation result).

    In dry-run mode (no API key) this returns an empty topic list plus a result
    pointing at the written prompt file.
    """
    client = client or AIClient()
    n = config.settings().get("content", {}).get("top_topics", 3)
    if not episode.transcript.strip():
        raise ValueError(f"Episode '{episode.slug}' has no transcript to analyze.")

    system, user = prompts.topics_prompt(episode.transcript, episode.host_notes, n)
    result = client.generate("topics", system, user, temperature=0.3)

    if result.dry_run:
        return [], result

    data = parse_json(result.text)
    topics = [Topic.model_validate(t) for t in data.get("topics", [])]
    return topics, result

"""Write a blog post that expands on an episode's top topics, in the host's voice."""

from __future__ import annotations

from ..models import Episode
from . import prompts
from .client import AIClient, GenerationResult


def write_blog(episode: Episode, client: AIClient | None = None) -> tuple[str, GenerationResult]:
    """Return blog markdown (and the raw generation result).

    Requires that topics have already been extracted (so the post has a backbone).
    In dry-run mode returns an empty string plus the prompt-file result.
    """
    client = client or AIClient()
    if not episode.topics:
        raise ValueError(
            f"Episode '{episode.slug}' has no topics yet. Run `topics` first "
            f"(or `run`, which does both)."
        )

    topics = [t.model_dump() for t in episode.topics]
    system, user = prompts.blog_prompt(episode.title, topics, episode.transcript)
    result = client.generate("blog", system, user)

    if result.dry_run:
        return "", result
    return result.text, result

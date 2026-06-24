"""Write social media copy for each highlight clip, per configured platform."""

from __future__ import annotations

from .. import config
from ..models import Clip, Episode
from . import prompts
from ._json import parse_json
from .client import AIClient, GenerationResult


def write_social_for_clip(
    episode: Episode, clip: Clip, client: AIClient | None = None
) -> tuple[dict[str, str], GenerationResult]:
    """Return {platform: copy} for one clip (and the raw generation result)."""
    client = client or AIClient()
    content_cfg = config.settings().get("content", {})
    platforms = content_cfg.get("social_platforms", ["linkedin", "youtube", "shorts"])
    hashtags = content_cfg.get("hashtags", {"enabled": True, "max": 5})

    system, user = prompts.social_prompt(episode.title, clip.model_dump(), platforms, hashtags)
    result = client.generate("social", system, user)

    if result.dry_run:
        return {}, result

    data = parse_json(result.text)
    # Keep only string values for the requested platforms.
    social = {p: str(data[p]).strip() for p in platforms if p in data}
    return social, result


def write_social(episode: Episode, client: AIClient | None = None) -> tuple[int, list[GenerationResult]]:
    """Generate social copy for every clip on the episode (mutates the clips).

    Returns (number_of_clips_processed, [results]).
    """
    client = client or AIClient()
    if not episode.clips:
        raise ValueError(
            f"Episode '{episode.slug}' has no clips. Add some with "
            f"`podcast-insight clips add {episode.slug} --title ... --start ... --end ...`"
        )
    results: list[GenerationResult] = []
    for clip in episode.clips:
        social, result = write_social_for_clip(episode, clip, client)
        if social:
            clip.social = social
        results.append(result)
    return len(episode.clips), results

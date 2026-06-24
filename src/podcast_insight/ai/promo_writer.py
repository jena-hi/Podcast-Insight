"""Write a social caption that promotes the blog post (not a per-clip caption)."""

from __future__ import annotations

from .. import config
from ..models import Episode
from . import prompts
from ._json import parse_json
from .client import AIClient, GenerationResult


def write_promo(episode: Episode, client: AIClient | None = None) -> tuple[dict[str, str], GenerationResult]:
    """Return {platform: caption} promoting the blog (and the raw result).

    Requires a blog to exist. In dry-run mode returns {} plus the prompt result.
    """
    client = client or AIClient()
    if not episode.blog_markdown:
        raise ValueError(
            f"Episode '{episode.slug}' has no blog yet. Run `blog` (or `from-youtube`) first."
        )
    content_cfg = config.settings().get("content", {})
    platforms = content_cfg.get("promo_platforms", ["linkedin"])
    hashtags = content_cfg.get("hashtags", {"enabled": True, "max": 5})
    topics = [t.model_dump() for t in episode.topics]

    system, user = prompts.promo_prompt(episode.title, episode.blog_markdown, topics, platforms, hashtags)
    result = client.generate("social", system, user)

    if result.dry_run:
        return {}, result
    data = parse_json(result.text)
    promo = {p: str(data[p]).strip() for p in platforms if p in data}
    return promo, result

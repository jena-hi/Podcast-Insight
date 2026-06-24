"""Generate TikTok video specs (storyboard + voiceover + caption) per topic."""

from __future__ import annotations

from .. import config
from ..ai import prompts
from ..ai._json import parse_json
from ..ai.client import AIClient, GenerationResult
from ..models import Episode
from .models import Scene, TikTokVideo


def generate_for_topic(
    episode: Episode, topic_index: int, client: AIClient | None = None
) -> tuple[TikTokVideo | None, GenerationResult]:
    """Generate one TikTok spec for the topic at `topic_index`."""
    client = client or AIClient()
    topic = episode.topics[topic_index]
    bv = config.brand_visual().get("video", {})
    duration = int(bv.get("duration_seconds", 15))
    hashtags_max = config.settings().get("content", {}).get("hashtags", {}).get("max", 5)

    system, user = prompts.tiktok_prompt(topic.model_dump(), episode.title, duration, hashtags_max)
    result = client.generate("tiktok", system, user)
    if result.dry_run:
        return None, result

    data = parse_json(result.text)
    video = TikTokVideo(
        topic_title=topic.title,
        episode_slug=episode.slug,
        hook=data.get("hook", ""),
        scenes=[Scene.model_validate(s) for s in data.get("scenes", [])],
        voiceover_script=data.get("voiceover_script", ""),
        caption=data.get("caption", ""),
        hashtags=data.get("hashtags", []),
        music_mood=data.get("music_mood", ""),
    )
    return video, result


def generate_all(
    episode: Episode, client: AIClient | None = None
) -> tuple[list[TikTokVideo], list[GenerationResult]]:
    """Generate a TikTok spec for each of the episode's topics."""
    client = client or AIClient()
    if not episode.topics:
        raise ValueError(
            f"Episode '{episode.slug}' has no topics yet. Run `topics` (or `run`) first."
        )
    videos: list[TikTokVideo] = []
    results: list[GenerationResult] = []
    for i in range(len(episode.topics)):
        video, result = generate_for_topic(episode, i, client)
        results.append(result)
        if video:
            videos.append(video)
    return videos, results

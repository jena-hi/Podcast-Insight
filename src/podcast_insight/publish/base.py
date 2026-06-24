"""Publisher interface + stubs for LinkedIn and YouTube.

Each publisher takes already-generated content and posts it. They raise
NotImplementedError until you wire them up — on purpose, so nothing posts to a
live account by accident.
"""

from __future__ import annotations

from typing import Protocol

from ..models import Clip, Episode


class Publisher(Protocol):
    name: str

    def publish_blog(self, episode: Episode) -> str: ...
    def publish_clip(self, episode: Episode, clip: Clip) -> str: ...


class LinkedInPublisher:
    """Post blog + clip copy to LinkedIn.

    Note: this project already has LinkedIn tooling available via the
    'ConnectSafely' MCP integration (see docs/AUTOMATION.md) — you may prefer to
    drive posting through that rather than the raw LinkedIn API.
    """

    name = "linkedin"

    def publish_blog(self, episode: Episode) -> str:
        raise NotImplementedError("LinkedIn publishing not wired up — see docs/AUTOMATION.md.")

    def publish_clip(self, episode: Episode, clip: Clip) -> str:
        raise NotImplementedError("LinkedIn publishing not wired up — see docs/AUTOMATION.md.")


class YouTubePublisher:
    """Update YouTube clip title/description from generated social copy."""

    name = "youtube"

    def publish_clip(self, episode: Episode, clip: Clip) -> str:
        raise NotImplementedError("YouTube publishing not wired up — see docs/AUTOMATION.md.")

    def publish_blog(self, episode: Episode) -> str:  # not applicable
        raise NotImplementedError("YouTube has no blog target.")

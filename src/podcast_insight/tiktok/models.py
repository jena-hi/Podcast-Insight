"""Models for a 15-second branded TikTok video spec."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class Scene(BaseModel):
    """One on-screen beat of the video."""

    role: str                          # "hook" | "point" | "cta"
    start: float                       # seconds
    duration: float                    # seconds
    on_screen_text: str                # short, punchy, fits a phone screen
    visual: str = ""                   # background/motion note (uses brand palette)


class TikTokVideo(BaseModel):
    """A complete spec for one topic's TikTok."""

    topic_title: str
    episode_slug: Optional[str] = None
    hook: str = ""                     # the opening line (also scene 1 text)
    scenes: list[Scene] = Field(default_factory=list)
    voiceover_script: str = ""         # ~40 words, ~15s read aloud
    caption: str = ""                  # the TikTok post caption
    hashtags: list[str] = Field(default_factory=list)
    music_mood: str = ""               # suggested background music vibe
    voiceover_audio_path: Optional[str] = None   # set if TTS was synthesized

    @property
    def total_duration(self) -> float:
        return round(sum(s.duration for s in self.scenes), 1)

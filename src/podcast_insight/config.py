"""Loading of settings, the voice profile, and environment variables.

Everything in here is read-only configuration. Paths are resolved relative to the
project root so the tool works no matter which directory you run it from.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

# Project root = two levels up from this file (src/podcast_insight/config.py).
PROJECT_ROOT = Path(__file__).resolve().parents[2]

CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
EPISODES_DIR = DATA_DIR / "episodes"
ANALYTICS_DIR = DATA_DIR / "analytics"
OUTPUT_DIR = DATA_DIR / "output"
# LinkedIn raw data — git-ignored because it holds PII (commenter/attendee names).
LINKEDIN_DIR = DATA_DIR / "linkedin"
# Git-tracked, publishable per-episode deliverables (blog/promo/social/tiktok).
CONTENT_DIR = PROJECT_ROOT / "content"
# Git-tracked reports the monthly cloud job commits (insights over time).
REPORTS_DIR = PROJECT_ROOT / "reports"

SETTINGS_FILE = CONFIG_DIR / "settings.yaml"
VOICE_PROFILE_FILE = CONFIG_DIR / "voice_profile.yaml"
BRAND_VISUAL_FILE = CONFIG_DIR / "brand_visual.yaml"

# Load .env once, on import, so os.getenv works everywhere.
load_dotenv(PROJECT_ROOT / ".env")


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


@lru_cache(maxsize=1)
def settings() -> dict[str, Any]:
    """The parsed contents of config/settings.yaml."""
    return _read_yaml(SETTINGS_FILE)


@lru_cache(maxsize=1)
def voice_profile() -> dict[str, Any]:
    """The parsed contents of config/voice_profile.yaml."""
    return _read_yaml(VOICE_PROFILE_FILE)


@lru_cache(maxsize=1)
def brand_visual() -> dict[str, Any]:
    """The parsed contents of config/brand_visual.yaml (fonts/colors/video)."""
    return _read_yaml(BRAND_VISUAL_FILE)


def read_config_text(filename: str) -> str:
    """Read a text/markdown file from the config/ directory (e.g. brand_voice.md).

    Returns "" if the file is missing so callers can treat it as optional.
    """
    if not filename:
        return ""
    path = CONFIG_DIR / filename
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def env(name: str, default: str | None = None) -> str | None:
    """Read an environment variable (from .env or the shell)."""
    value = os.getenv(name, default)
    # Treat empty strings as "not set" so blank .env lines behave predictably.
    return value if value else default


def model_for(task: str) -> str:
    """Resolve which AI model to use for a task, honoring per-task overrides."""
    ai = settings().get("ai", {})
    overrides = ai.get("overrides", {}) or {}
    override = overrides.get(task)
    if override:
        return override
    return ai.get("model", "claude-sonnet-4-6")


def ensure_dirs() -> None:
    """Create the data directories if they don't exist yet."""
    for d in (EPISODES_DIR, ANALYTICS_DIR, OUTPUT_DIR, LINKEDIN_DIR, CONTENT_DIR, REPORTS_DIR):
        d.mkdir(parents=True, exist_ok=True)

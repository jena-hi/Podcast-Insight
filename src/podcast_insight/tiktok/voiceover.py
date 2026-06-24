"""Optional text-to-speech for the voiceover.

This is OFF by default. The codebase always produces the voiceover *script*; this
turns it into an audio file only if you configure a TTS provider. There is no free
Anthropic TTS, so this uses any OpenAI-compatible /audio/speech endpoint (OpenAI,
or a compatible/self-hosted one). It's optional and the only paid piece — leave it
unset to just use the script (record it yourself, or let Canva read it).

Config (.env):
  TTS_API_KEY     provider key (required to enable)
  TTS_BASE_URL    default https://api.openai.com/v1
  TTS_MODEL       default "gpt-4o-mini-tts"
  TTS_VOICE       default "alloy"
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Optional

from .. import config


def enabled() -> bool:
    return bool(config.env("TTS_API_KEY"))


def synthesize(text: str, out_path: Path) -> Optional[Path]:
    """Synthesize `text` to an mp3 at `out_path`. Returns the path, or None if
    TTS isn't configured. Raises only on an actual provider error."""
    api_key = config.env("TTS_API_KEY")
    if not api_key or not text.strip():
        return None

    base = config.env("TTS_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = config.env("TTS_MODEL", "gpt-4o-mini-tts")
    voice = config.env("TTS_VOICE", "alloy")

    body = json.dumps({
        "model": model,
        "voice": voice,
        "input": text,
        "response_format": "mp3",
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{base}/audio/speech",
        data=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310
        out_path.write_bytes(resp.read())
    return out_path

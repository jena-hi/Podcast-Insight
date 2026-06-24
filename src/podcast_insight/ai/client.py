"""A thin wrapper around the Claude API with a no-key 'dry-run' fallback.

Design goals:
  * If ANTHROPIC_API_KEY is set, call the API and return finished text.
  * If it isn't, don't fail — write the fully-rendered prompt to a file so you
    can paste it into Claude yourself (or just review what would be sent). This
    lets the whole pipeline run end-to-end before you set up a key.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .. import config


@dataclass
class GenerationResult:
    """What a generation call returns, whether real or dry-run."""

    text: str                       # finished output, OR a note in dry-run mode
    dry_run: bool
    prompt_path: Optional[Path] = None   # where the prompt was written (dry-run)
    model: Optional[str] = None


class AIClient:
    """Generates text with Claude, or emits prompts when no key is present."""

    def __init__(self) -> None:
        self.api_key = config.env("ANTHROPIC_API_KEY")
        self._client = None  # lazily created so the import stays cheap

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def _ensure_client(self):
        if self._client is None:
            try:
                from anthropic import Anthropic
            except ImportError as exc:  # pragma: no cover
                raise RuntimeError(
                    "The 'anthropic' package isn't installed. Run: pip install -e ."
                ) from exc
            self._client = Anthropic(api_key=self.api_key)
        return self._client

    def generate(
        self,
        task: str,
        system: str,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> GenerationResult:
        """Run one generation.

        `task` names the step (topics/blog/social/insights) — it picks the model
        override and the dry-run filename.
        """
        ai_cfg = config.settings().get("ai", {})
        model = config.model_for(task)
        max_tokens = max_tokens or ai_cfg.get("max_tokens", 4096)
        temperature = (
            temperature if temperature is not None else ai_cfg.get("temperature", 0.7)
        )

        if not self.enabled:
            return self._dry_run(task, system, prompt, model)

        client = self._ensure_client()
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(
            block.text for block in message.content if block.type == "text"
        ).strip()
        return GenerationResult(text=text, dry_run=False, model=model)

    def _dry_run(self, task: str, system: str, prompt: str, model: str) -> GenerationResult:
        prompts_dir = config.OUTPUT_DIR / "prompts"
        prompts_dir.mkdir(parents=True, exist_ok=True)
        path = prompts_dir / f"{task}.md"
        rendered = (
            f"# Prompt for: {task}\n"
            f"# Model that would be used: {model}\n"
            f"# (Dry-run — no ANTHROPIC_API_KEY set. Paste this into Claude, or "
            f"add a key to .env and re-run for automatic output.)\n\n"
            f"## SYSTEM\n\n{system}\n\n"
            f"## USER\n\n{prompt}\n"
        )
        path.write_text(rendered, encoding="utf-8")
        note = (
            f"[dry-run] No API key set — wrote prompt to {path.relative_to(config.PROJECT_ROOT)}"
        )
        return GenerationResult(text=note, dry_run=True, prompt_path=path, model=model)

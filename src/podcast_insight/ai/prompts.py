"""Prompt templates for every AI step.

Kept in one place so you can read and tweak the exact wording without digging
through code. Each function returns a (system, user) tuple.
"""

from __future__ import annotations

import json
from typing import Any

from .. import config


def _voice_block() -> str:
    """Render the voice profile into a compact instruction block."""
    vp = config.voice_profile()
    if not vp:
        return "No voice profile configured; write in a clear, professional tone."

    def fmt(value: Any) -> str:
        if isinstance(value, list):
            return ", ".join(str(v) for v in value)
        return str(value).strip()

    lines = [
        f"Host: {vp.get('host_name', 'the host')}",
        f"Podcast: {vp.get('podcast_name', '')}",
        f"Bio: {fmt(vp.get('bio', ''))}",
        f"Audience: {fmt(vp.get('audience', ''))}",
        f"Tone: {fmt(vp.get('tone', ''))}",
    ]
    style = vp.get("style", {}) or {}
    for k, v in style.items():
        lines.append(f"Style — {k.replace('_', ' ')}: {fmt(v)}")
    if vp.get("signature_phrases"):
        lines.append(f"Signature phrases (use naturally, don't overdo): {fmt(vp['signature_phrases'])}")
    if vp.get("avoid"):
        lines.append(f"Strictly AVOID: {fmt(vp['avoid'])}")
    fm = vp.get("formatting", {}) or {}
    rules = []
    if fm.get("oxford_comma"):
        rules.append("always use the Oxford comma")
    if fm.get("headings_case"):
        rules.append(f"headings in {fm['headings_case']}")
    if fm.get("numbers"):
        rules.append(f"numbers: {fm['numbers']}")
    if "max_exclamations" in fm:
        rules.append(f"at most {fm['max_exclamations']} exclamation mark(s) per piece")
    if rules:
        lines.append("Formatting rules: " + "; ".join(rules) + ".")

    inline = fmt(vp.get("writing_samples", ""))
    if inline and "Paste" not in inline:
        lines.append(f"\nReal writing samples to match in voice and rhythm:\n{inline}")

    block = "\n".join(line for line in lines if line.strip().rstrip(":"))

    # Inject the authoritative brand guide verbatim — it always wins on conflicts.
    guide = config.read_config_text(vp.get("brand_guide_file", ""))
    if guide:
        block += (
            "\n\n=== AUTHORITATIVE BRAND VOICE GUIDE (follow exactly; it overrides "
            "anything above on conflict) ===\n" + guide
        )

    # Inject real example posts as few-shot voice references.
    sample_files = vp.get("sample_files", []) or []
    sample_texts = [t for f in sample_files if (t := config.read_config_text(f))]
    if sample_texts:
        block += (
            "\n\n=== EXAMPLE POSTS (match this exact voice, rhythm, and structure; "
            "do not copy their content) ===\n" + "\n\n".join(sample_texts)
        )

    return block


# ── Topic extraction ─────────────────────────────────────────────────────────

def topics_prompt(transcript: str, host_notes: str, n: int) -> tuple[str, str]:
    system = (
        "You are an expert podcast producer. You read a transcript and identify "
        "the most substantive, audience-valuable topics actually discussed — not "
        "filler, intros, or sign-offs. You are precise and never invent content."
    )
    notes = f"\n\nHOST NOTES (use as a hint to priorities):\n{host_notes}" if host_notes.strip() else ""
    user = (
        f"From the transcript below, identify the TOP {n} topics, ranked by how "
        f"valuable and discussion-worthy they are for the audience.\n\n"
        f"Return ONLY valid JSON, no prose, in exactly this shape:\n"
        f'{{"topics": [{{"title": "...", "summary": "1-2 sentences", '
        f'"key_points": ["...", "..."], "timestamp": "MM:SS or null"}}]}}\n\n'
        f"Rules:\n"
        f"- Exactly {n} topics.\n"
        f"- key_points: 2-4 concrete points each, drawn from what was actually said.\n"
        f"- timestamp: the rough start of the discussion if visible, else null.\n"
        f"- Do not include the intro greeting or the outro/sign-off as a topic."
        f"{notes}\n\nTRANSCRIPT:\n{transcript}"
    )
    return system, user


# ── Blog ─────────────────────────────────────────────────────────────────────

def blog_prompt(title: str, topics: list[dict], transcript: str) -> tuple[str, str]:
    vp = config.voice_profile()
    fmt = vp.get("formatting", {}) or {}
    target_len = fmt.get("target_length_words", 900)
    system = (
        "You are a ghostwriter who writes blog posts that sound exactly like the "
        "host. Match their voice precisely. Expand on ideas with genuine insight, "
        "but never invent facts, statistics, or quotes that aren't supported by "
        "the episode.\n\nVOICE PROFILE:\n" + _voice_block()
    )
    topics_json = json.dumps(topics, indent=2)
    extras = []
    if fmt.get("use_headings", True):
        extras.append("Use clear section headings (one per top topic).")
    if fmt.get("include_intro_hook", True):
        extras.append("Open with a hook that earns the next sentence — no generic 'In today's world' opener.")
    if fmt.get("include_call_to_action", True):
        extras.append("End with a short CTA to listen to the full episode and subscribe.")
    extras_block = "\n".join(f"- {e}" for e in extras)
    user = (
        f"Write a blog post for the episode titled \"{title}\".\n\n"
        f"Expand on these top topics (this is the backbone of the post):\n"
        f"{topics_json}\n\n"
        f"Guidance:\n"
        f"- Target ~{target_len} words.\n"
        f"- Lead with the single most interesting idea, not a summary of the episode.\n"
        f"- For each topic: the takeaway first, then why it matters, then a concrete example or application.\n"
        f"{extras_block}\n"
        f"- Output clean Markdown (a top-level # title, then ## sections).\n\n"
        f"Use the transcript only as ground truth for what was actually said:\n\n{transcript}"
    )
    return system, user


# ── Social ───────────────────────────────────────────────────────────────────

def social_prompt(
    episode_title: str,
    clip: dict,
    platforms: list[str],
    hashtags_cfg: dict,
) -> tuple[str, str]:
    system = (
        "You write scroll-stopping but honest social copy for podcast clips. You "
        "match the host's voice and never overpromise or clickbait dishonestly.\n\n"
        "VOICE PROFILE:\n" + _voice_block()
    )
    ht = ""
    if hashtags_cfg.get("enabled", True):
        ht = f"Include up to {hashtags_cfg.get('max', 5)} relevant hashtags where the platform expects them (LinkedIn: few; YouTube: in description; Shorts: in caption)."

    platform_specs = {
        "linkedin": "LinkedIn post: 2-4 short paragraphs, a strong first line (the 'hook' shown before 'see more'), conversational, ends with a question or light CTA.",
        "youtube": "YouTube clip upload: a punchy <70-char title, then a 2-3 sentence description with a line pointing to the full episode.",
        "shorts": "Short vertical video caption: one punchy hook line (<100 chars) plus 1-2 line caption. Optimized for Shorts/Reels.",
    }
    wanted = "\n".join(f"- {p}: {platform_specs.get(p, p)}" for p in platforms)
    keys = ", ".join(f'"{p}"' for p in platforms)
    user = (
        f"Episode: \"{episode_title}\"\n"
        f"Clip title: {clip.get('title')}\n"
        f"Clip timestamps: {clip.get('start')}–{clip.get('end')}\n"
        f"Why this clip matters (host note): {clip.get('note') or '(none given)'}\n"
        f"Clip transcript excerpt: {clip.get('transcript_excerpt') or '(none provided)'}\n\n"
        f"Write copy for these platforms:\n{wanted}\n\n{ht}\n\n"
        f"Return ONLY valid JSON keyed by platform, e.g. {{{keys}: \"...\"}}. "
        f"No commentary outside the JSON."
    )
    return system, user


# ── Blog promo caption ───────────────────────────────────────────────────────

def promo_prompt(
    episode_title: str,
    blog_markdown: str,
    topics: list[dict],
    platforms: list[str],
    hashtags_cfg: dict,
) -> tuple[str, str]:
    system = (
        "You write social captions that drive people to read a blog post. You "
        "match the host's voice exactly, tease the single most compelling idea, "
        "and never overpromise or clickbait dishonestly.\n\n"
        "VOICE PROFILE:\n" + _voice_block()
    )
    ht = ""
    if hashtags_cfg.get("enabled", True):
        ht = f"Include up to {hashtags_cfg.get('max', 5)} relevant hashtags."
    keys = ", ".join(f'"{p}"' for p in platforms)
    topics_json = json.dumps(topics, indent=2)
    user = (
        f"Write a caption (or captions) promoting the blog post for the episode "
        f"\"{episode_title}\".\n\n"
        f"The post's backbone topics:\n{topics_json}\n\n"
        f"Goal: get the reader to click through and read the post. Lead with the "
        f"sharpest hook, tease one core idea (don't summarize everything), end "
        f"with a clear CTA to read the blog. Use a placeholder '[BLOG LINK]' where "
        f"the link goes.\n{ht}\n\n"
        f"Write one caption per platform: {', '.join(platforms)}.\n"
        f"Return ONLY valid JSON keyed by platform, e.g. {{{keys}: \"...\"}}. "
        f"No commentary outside the JSON.\n\n"
        f"For reference, here is the blog post:\n\n{blog_markdown}"
    )
    return system, user


# ── Insights ─────────────────────────────────────────────────────────────────

def insights_prompt(scored_summary: str) -> tuple[str, str]:
    system = (
        "You are a sharp content strategist for podcasters. You read performance "
        "data and give specific, honest, actionable advice. You distinguish "
        "correlation from causation, and you never pad with generic tips."
    )
    user = (
        "Below is performance data across the podcast's episodes and clips, with a "
        "combined score per episode. Analyze it and produce:\n\n"
        "1. **Top performers** — what they have in common (topic, length, format, title style, guest, timing).\n"
        "2. **Underperformers** — likely reasons, stated as hypotheses not certainties.\n"
        "3. **What's working / what's not** — concrete patterns.\n"
        "4. **Recommendations** — 5-8 specific, prioritized actions for upcoming episodes and clips.\n\n"
        "Be specific to THIS data. Output clean Markdown.\n\n"
        f"DATA:\n{scored_summary}"
    )
    return system, user

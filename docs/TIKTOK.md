# TikTok layer — 15-second branded videos per topic

For each episode, this turns the **top 3 topics** into three 15-second vertical
(9:16) TikToks in the *Unscripted Intelligence* brand: a **branded motion-text**
video with an **AI voiceover + music**, plus a ready-to-post caption.

Two halves, by design:

1. **The codebase generates the plan** (free, deterministic, on-brand):
   - a 15-second **storyboard** (hook → point → CTA scenes, with on-screen text
     and timing),
   - a **voiceover script** (~40 words, ~15s read aloud),
   - a **caption** + hashtags in the brand voice.
2. **Canva renders + exports the video** (in a Claude session), using your brand
   colors/fonts from `config/brand_visual.yaml`.

---

## Step 1 — generate the scripts

```bash
podcast-insight tiktok <episode-slug>
```

Output lands in `data/output/tiktok/<slug>/`:
- `topic-1.json`, `topic-2.json`, `topic-3.json` — full specs (storyboard, etc.)
- `summary.md` — human-readable, all three
- `topic-N-voiceover.mp3` — only if TTS is configured (see below)

This needs the episode's topics, so run `topics`/`run`/`from-youtube` first.

## Step 2 — voiceover audio (optional, the only paid bit)

The script is always generated. To get **audio**, set a TTS provider in `.env`
(`TTS_API_KEY`, etc. — any OpenAI-compatible endpoint; there's no free Anthropic
TTS). Without it, you get the script to record yourself or have Canva read.

## Step 3 — render in Canva (in a Claude session)

Canva is the connected render tool. In a Claude session, say something like:

> "Build the TikToks for <episode> in Canva and export them."

Claude will, via the Canva connector:
1. Ensure a brand kit / template exists from `config/brand_visual.yaml` (fonts
   Michroma + Roboto, the magenta/purple palette, logo).
2. For each `topic-N.json`, create a 1080×1920 video: animate the scenes'
   on-screen text on brand backgrounds, add the voiceover audio (if present) and
   background music matching `music_mood`.
3. Export each as MP4 to `data/output/tiktok/<slug>/`.

Then review and post to your TikTok channel.

### Honest limits
- This produces **motion-text / graphic** videos, not edits of your actual
  podcast footage (that's the Descript work you do by hand).
- Canva's MCP video capabilities evolve; some animation/export features need
  **Canva Pro**. If an export option is missing, Claude will tell you and fall
  back to exporting frames / a simpler design.
- Always eyeball each video before posting — fonts/spacing on auto-built designs
  sometimes need a nudge.

---

## Brand inputs

Everything visual comes from `config/brand_visual.yaml` (captured from your brand
guide). Confirm the **hex values** there (they were eyeballed from the PDF
swatches) and add your **logo** path/URL so Canva can place it.

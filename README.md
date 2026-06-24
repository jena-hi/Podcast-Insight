# Podcast Insight

An automation toolkit for a live podcast workflow (LinkedIn Live → YouTube →
Spotify/Apple). It turns each episode into **content** and **insight**:

1. **Content engine** *(working today)*
   - Extracts the **top 3 topics** of an episode from its transcript.
   - Writes a **blog post** that expands on those topics, in *your voice*
     (defined in a voice profile).
   - Writes **social media copy** (LinkedIn + YouTube + shorts captions) for the
     highlight clips you cut.
2. **Analytics + insights** *(scaffolded, ready to wire up)*
   - Pulls performance data from **YouTube** and **Spotify/Apple**.
   - Ranks your **top-performing** episodes and clips.
   - Generates **recommendations**: what worked, what didn't, what to do next.

> What this does **not** do: it does not record, cut, or edit your video
> (StreamYard / Descript stay manual). It picks up *after* you have a transcript
> and your clip list, and it handles everything text/analysis/insight.

---

## How the whole thing fits together

```
  LinkedIn Live ──► YouTube (auto)         You cut clips in StreamYard
        │                                          │
        ▼                                          ▼
   Transcript + host notes ───────────►  Clip list (title, start, end)
        │                                          │
        ▼                                          ▼
 ┌──────────────────────── Podcast Insight ───────────────────────┐
 │                                                                 │
 │  ingest ─► topics ─► blog            social  ◄── (per clip)     │
 │                       │                 │                       │
 │                       ▼                 ▼                       │
 │                  data/output/blog/  data/output/social/         │
 │                                                                 │
 │  analytics pull ─► YouTube / Spotify / Apple ─► insights        │
 │                                                   │             │
 │                                                   ▼             │
 │                                       data/output/insights/     │
 └─────────────────────────────────────────────────────────────────┘
        │                       │                      │
        ▼                       ▼                      ▼
  Paste into blog        Paste into LinkedIn/    Decide what to make
  (or auto-publish       YouTube (or auto-       more / less of next
   later)                 publish later)          episode
```

The pieces are deliberately separate so you can run one at a time, and so the
"publish automatically" parts can be switched on later without rewriting
anything.

---

## Quick start (5 minutes, no API key needed)

You need **Python 3.10+**. Check with `python3 --version`.

```bash
# 1. From the project folder, create an isolated environment and install
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e .

# 2. Copy the config template (you can edit it later)
cp .env.example .env

# 3. Try it on the included sample episode — runs in "dry-run" mode,
#    which writes the exact prompts to files instead of calling the AI.
podcast-insight ingest examples/sample_episode.md \
    --title "How AI Is Changing Sales" --date 2026-06-10
podcast-insight run how-ai-is-changing-sales
```

Look in `data/output/` — you'll see the topics, a blog draft prompt, and social
copy prompts. In dry-run mode these are the *prompts* (so you can paste them into
Claude yourself, or just review them). Add an API key (next section) and the same
commands produce finished text automatically.

---

## Turning on real AI generation

The content engine uses **Claude** (Anthropic's API). To switch from dry-run to
real output:

1. Get an API key at https://console.anthropic.com → **API Keys**.
2. Open `.env` and set:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```
3. Re-run `podcast-insight run <episode>`. Now `data/output/` contains finished
   blog drafts and social posts.

Cost is small — a full episode (topics + blog + social for ~5 clips) is well
under a dollar on the default model. See `config/settings.yaml` to switch models
(e.g. a cheaper one for drafts, a stronger one for final blogs).

---

## Make it sound like *you* — the voice profile

The voice is driven by three files in `config/`, and all of them are injected
into every blog and social generation:

- **`voice_profile.yaml`** — the structured essentials (host, audience, tone,
  signature phrases, hard rules, formatting). Already filled in for the Human
  Intelligence Movement / *Unscripted Intelligence*.
- **`brand_voice.md`** — the full, authoritative brand voice guide. This is the
  canon; on any conflict it wins. Edit this when the brand voice evolves.
- **`caption_samples.md`** — real approved posts used as few-shot examples so the
  social copy matches your actual rhythm and structure.

To adapt for a different show, edit these three files. `voice_profile.yaml`
points at the other two via `brand_guide_file` and `sample_files`.

---

## The commands

| Command | What it does |
|---|---|
| `podcast-insight ingest <file> --title ... --date ...` | Register an episode from a transcript file. |
| `podcast-insight topics <episode>` | Extract & rank the top 3 topics. |
| `podcast-insight blog <episode>` | Write a blog expanding the top 3 topics, in your voice. |
| `podcast-insight clips add <episode> ...` | Add a highlight clip (title, timestamps, note). |
| `podcast-insight social <episode>` | Write social copy for each clip. |
| `podcast-insight run <episode>` | Do topics → blog → social in one go. |
| `podcast-insight analytics pull <episode>` | Pull YouTube/Spotify/Apple stats. *(needs API setup)* |
| `podcast-insight insights` | Rank top performers + recommendations across all episodes. |
| `podcast-insight list` | Show all episodes and what's been generated. |

Run any command with `--help` for details.

---

## Where things live

```
config/        Your settings + voice profile (edit these)
data/
  episodes/    One JSON file per episode (the "database")
  analytics/   Raw stats pulled from each platform
  output/      Everything generated: blog/, social/, insights/
examples/      A sample episode so you can try it immediately
src/podcast_insight/
  ai/          Topic extraction, blog writer, social writer, Claude client
  analytics/   YouTube / Spotify / Apple connectors + insights engine
  ingest/      Reading transcripts/notes
  publish/     (Stubs) auto-posting hooks for later
```

---

## Roadmap — what's wired vs. what's next

- [x] Episode ingest + storage
- [x] Top-3 topic extraction
- [x] Voice-profiled blog writer
- [x] Per-clip social copy (LinkedIn / YouTube / shorts)
- [x] Insights + recommendations engine (works on whatever analytics it's given)
- [~] Analytics connectors — structured + documented; need your API credentials
      to pull live data (see `docs/CONNECTING_ANALYTICS.md`)
- [ ] Auto-publishing to LinkedIn / YouTube (stubs in `publish/`)
- [ ] Scheduling (run automatically after each episode)

See `docs/CONNECTING_ANALYTICS.md` and `docs/AUTOMATION.md` for the next steps,
each written for someone who's done "some API and coding stuff."

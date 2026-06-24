# Automation & publishing — the next steps

The scaffold runs on demand today. This is the recommended path to make it
hands-off, in order of effort/risk. Do them when you're ready; each is optional.

## Where your manual steps fit

Your current flow and where the tool plugs in:

| Step | Who does it | Tool involvement |
|---|---|---|
| Host LinkedIn Live → auto to YouTube | You / StreamYard | — |
| Cut clips | You (StreamYard) | — |
| Edit clips | You (Descript) | — |
| Get transcript | Export from YouTube/Descript/Otter | input to `ingest` |
| **Topics + blog + social copy** | **Podcast Insight** | `run` |
| Post clips + blog | You (for now) | copy from `data/output/` |
| Post to Spotify/Apple | You (Spotify for Creators) | — |
| **Analytics + insights** | **Podcast Insight** | `analytics pull`, `insights` |

So the tool owns the two highest-leverage, most tedious parts: turning a
transcript into publish-ready content, and turning scattered stats into a
prioritized to-do list.

## 1. Run it automatically after each episode

The simplest automation is a script you run once per episode that does ingest →
run, then you review the drafts. To go further:

- **Cron / scheduled job** (local or a small cloud box): a wrapper that watches a
  folder (e.g. a Google Drive synced folder where you drop the transcript), then
  runs the pipeline.
- **GitHub Actions**: this repo is already set up for Claude Code on the web. You
  could add a workflow that runs on a schedule or a manual trigger. Ask Claude
  Code to "add a GitHub Action that runs the pipeline on a transcript I commit to
  data/incoming/."

## 2. Auto-publishing (highest risk — do last)

Publishing is stubbed in `src/podcast_insight/publish/` on purpose — a bad
auto-post is hard to undo. Recommended order:

1. **YouTube clip metadata** (lowest risk): use the generated title/description
   when you upload, or update an existing upload via the YouTube Data API.
2. **LinkedIn**: you have two options —
   - the official LinkedIn API (requires app review for posting), or
   - the **ConnectSafely** integration already available in this environment,
     which can create posts and pull LinkedIn analytics. Ask Claude Code to
     "draft LinkedIn posts from data/output/social via ConnectSafely" and review
     before it posts.
3. Always keep a **review step** (`--dry-run` / draft mode) before anything goes
   live until you trust it.

## 3. Other integrations available in this environment

This Claude Code environment has connectors that fit your workflow:

- **ConnectSafely** — LinkedIn posting + analytics (followers, engagement, post
  reactions). Good for both publishing clips and pulling LinkedIn performance to
  fold into `insights`.
- **Canva** — auto-generate clip thumbnails / quote cards from your top topics.
- **Google Drive / Gmail / Calendar** — e.g. drop transcripts in Drive to
  trigger the pipeline, or email yourself the weekly insights report.

These aren't wired into the codebase yet, but they're available to Claude Code —
when you want one, just ask and it can build the integration against this
scaffold.

## Suggested "v2" priorities

1. Finish YouTube Analytics OAuth (real watch-time/retention → much better insights).
2. Wire LinkedIn analytics into `insights` (so cross-platform performance is one view).
3. Add a review-then-publish flow for LinkedIn + YouTube clip copy.
4. Schedule the whole thing off a transcript drop.

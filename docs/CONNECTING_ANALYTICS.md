# Connecting analytics (YouTube, Spotify, Apple)

This walks you through getting real numbers into Podcast Insight. You can do these
in any order, and the tool works fine with only one connected. Written for
someone who's done "some API and coding stuff" — nothing here assumes you're a
full-time developer.

The general flow for every episode:

```bash
# 1. tell the tool which video/episode this is on each platform
podcast-insight set my-episode-slug --youtube dQw4w9WgXcQ --spotify 5Xt...

# 2. pull the numbers
podcast-insight analytics pull my-episode-slug

# 3. once you have a few episodes, get insights
podcast-insight insights
```

---

## YouTube

There are **two levels** of YouTube data.

### Level 1 — public stats (easy, ~10 min): views, likes, comments

1. Go to https://console.cloud.google.com/ and create a project (free).
2. **APIs & Services → Library →** enable **"YouTube Data API v3"**.
3. **APIs & Services → Credentials → Create credentials → API key.**
4. Put it in `.env`:
   ```
   YOUTUBE_API_KEY=AIza...
   ```
5. For each episode, set the video id (the part after `watch?v=`):
   ```
   podcast-insight set my-slug --youtube dQw4w9WgXcQ
   ```

That's enough for views/likes/comments. It's already implemented.

### Level 2 — private analytics (more setup): watch time, retention, subs gained

These come from the **YouTube Analytics API**, which requires OAuth as the channel
owner (an API key isn't enough — these numbers are private to you).

1. In the same Google Cloud project, also enable **"YouTube Analytics API"**.
2. **Credentials → Create credentials → OAuth client ID →** Desktop app.
3. Download the client-secret JSON, save it somewhere in the project, and set:
   ```
   YOUTUBE_OAUTH_CLIENT_SECRET_FILE=secrets/yt_client_secret.json
   ```
4. Implement the OAuth flow in
   `src/podcast_insight/analytics/youtube.py → _maybe_add_private_analytics`.
   It's stubbed with a clear TODO and the exact fields to populate. (Ask Claude
   Code to "wire up YouTube Analytics OAuth" and it can finish this for you.)

> Why it's stubbed: OAuth needs your specific credentials to test, so it's left
> as the one piece you finish locally. Everything around it is ready.

---

## Spotify

Spotify splits into the same two levels.

### Public Web API (episode metadata) — implemented

1. Go to https://developer.spotify.com/dashboard → create an app.
2. Copy the **Client ID** and **Client Secret** into `.env`:
   ```
   SPOTIFY_CLIENT_ID=...
   SPOTIFY_CLIENT_SECRET=...
   ```
3. Set the episode id per episode (`set --spotify <episode_id>`). You get the id
   from the episode's Spotify URL.

### Deep listen analytics (streams, listeners, retention) — CSV export

Spotify's open API does **not** expose podcast listen analytics. The reliable
source is **Spotify for Creators** (formerly Anchor / Spotify for Podcasters):

1. In the Spotify for Creators dashboard, open your show → **Audience / Episodes**.
2. Export the data (CSV).
3. Save it under `data/analytics/` and finish the importer in
   `analytics/spotify.py → import_export_csv` (it's stubbed with the column
   mapping to fill in — the headers vary, so map them once from your real file).

---

## Apple Podcasts

Apple has **no open analytics API**. The supported path is the CSV export from
**Apple Podcasts Connect** — and this connector already reads it.

1. In Apple Podcasts Connect → **Trends / Analytics**, download the CSV export.
2. Save it in the folder named by `.env`:
   ```
   APPLE_PODCASTS_EXPORT_DIR=data/analytics/apple_exports
   ```
3. Make sure each episode's title matches the export, or set an explicit match:
   ```
   podcast-insight set my-slug --apple-title "Exact Title In Apple"
   ```
4. `podcast-insight analytics pull my-slug` will find the latest CSV and match by
   title. If Apple's column names differ, adjust `COLUMN_ALIASES` in
   `analytics/apple.py`.

---

## What "insights" does with all this

Once episodes have analytics, `podcast-insight insights`:

1. Aggregates each episode's metrics across platforms.
2. Normalizes and combines them into one score (weights in
   `config/settings.yaml → analytics.scoring_weights` — tune these).
3. Ranks episodes and asks Claude to explain *why* the top ones won and give
   prioritized recommendations.

You don't need every platform connected for this to be useful — even YouTube
public stats alone produce a meaningful ranking.

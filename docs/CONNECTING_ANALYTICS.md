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
3. Download the client-secret JSON, save it as `secrets/yt_client_secret.json`,
   and set in `.env`:
   ```
   YOUTUBE_OAUTH_CLIENT_SECRET_FILE=secrets/yt_client_secret.json
   ```
4. Install the analytics extras and run the one-time consent:
   ```bash
   pip install -e ".[analytics]"
   podcast-insight auth youtube
   ```
   A browser opens, you approve, and a token is saved to `secrets/`. From then on
   `analytics pull` automatically includes watch time, average view duration, and
   subscribers gained. **No further manual steps, ever.**

5. **For the monthly cloud job**, the command above also prints a **refresh
   token**. Store these three as GitHub repository secrets so the cloud job can
   run headless:
   ```
   YOUTUBE_OAUTH_CLIENT_ID
   YOUTUBE_OAUTH_CLIENT_SECRET
   YOUTUBE_OAUTH_REFRESH_TOKEN
   ```
   (Client id/secret are inside the client-secret JSON you downloaded.)

---

## Spotify for Creators (UNOFFICIAL)

> ⚠️ Spotify has **no official analytics API**. This connector reuses your
> logged-in browser session to call Spotify's own internal endpoints. It is
> undocumented, unsupported, and a gray area vs. Spotify's terms. It works, but
> it **will break periodically** when Spotify changes their dashboard, and you'll
> need to re-capture the request (or ask Claude Code to fix it). You opted into
> this trade-off.

You provide two things: a session cookie, and one captured analytics request.

### 1. Grab your `sp_dc` cookie (lasts ~1 year)

1. Log into https://creators.spotify.com in Chrome/Firefox.
2. Open **DevTools (F12) → Application (Chrome) or Storage (Firefox) → Cookies →
   the spotify.com entry**.
3. Find the cookie named **`sp_dc`** and copy its value.
4. Put it in `.env`:
   ```
   SPOTIFY_DC_COOKIE=<the long value>
   SPOTIFY_SHOW_ID=<your show id>
   ```

### 2. Capture one analytics request ("capture and replay")

Because the endpoints are undocumented, you point the tool at a real request
instead of guessing:

1. In the Creators dashboard, open an episode's analytics page.
2. DevTools → **Network** tab → filter to **Fetch/XHR**.
3. Click the request that returns the numbers you want (look for JSON with
   "streams", "starts", "listeners", etc.). Right-click → **Copy → Copy link
   address**.
4. Paste it into `.env`, replacing the episode/show ids with placeholders so the
   tool can reuse it for every episode:
   ```
   SPOTIFY_CREATORS_ANALYTICS_URL=https://generic.wg.spotify.com/.../shows/{show_id}/episodes/{episode_id}/detailedStreams
   ```
5. Set each episode's Spotify id: `podcast-insight set <slug> --spotify <episode_id>`.

Now `podcast-insight analytics pull <slug>` will mint a token from your cookie,
replay that request per episode, and pull the numbers automatically.

**If the JSON structure is unusual**, set `SPOTIFY_CREATORS_METRIC_KEYS` to the
exact key name(s) for plays/listens. Or paste a sample response to Claude Code and
ask it to map the fields — that's a 2-minute fix.

**For the monthly cloud job**, store `SPOTIFY_DC_COOKIE`, `SPOTIFY_SHOW_ID`, and
`SPOTIFY_CREATORS_ANALYTICS_URL` as GitHub secrets.

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

---

## Running it monthly, hands-off (GitHub Actions)

`.github/workflows/monthly-analytics.yml` runs on the 1st of each month (and on
demand from the Actions tab). It pulls every episode's analytics, regenerates the
insights report into `reports/`, and commits the results. It's free.

To turn it on:

1. Push this repo to GitHub (already done if you're reading this there).
2. Add your keys as **repository secrets**: Settings → Secrets and variables →
   Actions → New repository secret. Add whichever you use:
   `ANTHROPIC_API_KEY`, `YOUTUBE_API_KEY`, `YOUTUBE_OAUTH_CLIENT_ID`,
   `YOUTUBE_OAUTH_CLIENT_SECRET`, `YOUTUBE_OAUTH_REFRESH_TOKEN`,
   `SPOTIFY_DC_COOKIE`, `SPOTIFY_SHOW_ID`, `SPOTIFY_CREATORS_ANALYTICS_URL`.
3. Make sure your episode files are committed (they live in `data/episodes/` and
   are tracked in git). The `from-youtube` command tells you to do this.
4. Trigger a test run: Actions tab → "Monthly analytics + insights" → Run workflow.

Cost: a run takes ~2–5 minutes. Public repos get unlimited free Actions minutes;
private repos get 2,000 free minutes/month, so a monthly job is effectively free.
The only paid usage anywhere is a few cents of Claude tokens for the insights
write-up.

# Working in this repo (instructions for Claude)

This is **Podcast Insight** — it turns a podcast episode into a blog + social
copy, and pulls performance analytics. See `README.md` for the full picture.

## When the user pastes a YouTube link

If the user pastes a YouTube URL (or says "make content from this video"), treat
it as a request to run the content pipeline:

```bash
podcast-insight from-youtube "<the url>"
```

That fetches the transcript, extracts the top 3 topics, writes a blog post in the
brand voice, and writes a promo caption for the blog. Results land in
`data/output/` (blog, promo, topics).

Then:
1. Show the user the generated blog and the promo caption.
2. Ask if they want edits (tone, length, angle) and regenerate if so.
3. Remind them to commit the new episode file (`data/episodes/<slug>.json`) so
   the monthly analytics job can track it.

If `from-youtube` fails to get a transcript (YouTube blocks some cloud IPs), say
so plainly and suggest running it locally, or fall back to asking for a
transcript file and using `podcast-insight ingest`.

## Voice is non-negotiable

All blog/social generation must follow the brand voice in
`config/brand_voice.md` (authoritative), `config/voice_profile.yaml`, and the
examples in `config/caption_samples.md`. Key hard rules: no em dashes, Oxford
comma, sentence-case headings, "we" voice, never "soft skills" / "fix education"
/ fear framing. These are injected into prompts automatically — don't bypass them.

## Analytics

- `podcast-insight analytics pull <slug>` (or `pull-all`) pulls YouTube + Spotify.
- `podcast-insight insights` ranks episodes and writes recommendations to `reports/`.
- The monthly cloud job is `.github/workflows/monthly-analytics.yml`.
- Spotify uses an UNOFFICIAL session-cookie connector — if it errors, it likely
  needs the captured request URL re-grabbed (see docs/CONNECTING_ANALYTICS.md).

## Don't

- Don't commit `.env` or anything under `secrets/`.
- Don't post to any platform automatically without explicit confirmation.

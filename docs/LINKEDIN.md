# LinkedIn analytics layer

Two dashboards:

1. **Monthly page dashboard** — impressions, engagement rate, new followers (and
   reactions/comments/shares/posts), with month-over-month deltas. No personal
   data, so it's written to the git-tracked `reports/` folder.
2. **Per-event dashboard** — for each podcast you run as a LinkedIn Event:
   attendees, impressions, engagement rate, and **the list of people who
   commented** (name, headline, profile link, their comment). This contains
   personal data, so it's written **locally only** to `data/output/linkedin/`
   and is git-ignored.

Each event can be linked to an episode (`episode_slug`), so its impressions,
engagement, and attendees fold into the cross-platform `insights` ranking.

---

## Where the data comes from: ConnectSafely (in a Claude session)

LinkedIn has no free/official way to get event attendees or commenter names, so
this layer uses the **ConnectSafely** connector. Important: that connector is
available **inside a Claude session**, not to the cloud GitHub Actions job — so
LinkedIn pulls are run interactively (monthly), the same way `from-youtube` runs
locally.

### One-time setup

1. Your LinkedIn account is already linked to ConnectSafely (confirmed: *Jena
   Crossland*). Open the ConnectSafely dashboard and **allocate an API seat** to
   that account (this is the paid part). Until a seat is active, data pulls will
   be rejected.
2. **Page stats are pulled from a company page you manage, not your personal
   profile.** This account administers two pages:
   - **Human Intelligence Movement** — id `101674670` (the configured default)
   - **ProSolve** — id `691327`
   The target is set in `config/settings.yaml → linkedin`. To switch pages or add
   ProSolve too, edit that section.

### Monthly, in a Claude session

Just say, for example:

> "Pull this month's LinkedIn page analytics and import them."
>
> "Pull the LinkedIn event analytics for the *Real learning needs struggle*
> episode (event link: …) and import it."

Claude will use the ConnectSafely tools, map the results into the JSON shapes
below, and run the import commands for you. Then review the dashboards in
`reports/linkedin-page-*.md` and `data/output/linkedin/*.md`.

---

## Doing it manually (no ConnectSafely)

You can also build the dashboards from a manual export. Write a JSON file in the
shapes below and import it:

```bash
podcast-insight linkedin import-page  --file my_page.json
podcast-insight linkedin import-event --file my_event.json
podcast-insight linkedin list
```

### Page JSON  (see examples/linkedin_page.example.json)

```json
{
  "period": "2026-06",
  "impressions": 12450,
  "engagement_rate": 4.2,
  "new_followers": 85,
  "total_followers": 940,
  "reactions": 320, "comments": 64, "shares": 18, "posts": 9
}
```
`engagement_rate` is the **average monthly engagement rate** as a percent (4.2
means 4.2%) — this is the headline general-engagement metric. Any field can be
omitted.

> Events: the podcasts are hosted as LinkedIn Events on the **Human Intelligence
> Movement page**, so event pulls use that page as the host context.

### Event JSON  (see examples/linkedin_event.example.json)

```json
{
  "name": "Unscripted Intelligence — <topic>",
  "episode_slug": "real-learning-needs-struggle",
  "event_id": "https://www.linkedin.com/events/.../",
  "date": "2026-06-18",
  "attendees": 142, "registrants": 210,
  "impressions": 5400, "engagement_rate": 6.1,
  "reactions": 88, "comments_count": 23,
  "commenters": [
    {"name": "Jane Doe", "headline": "Director of Learning",
     "profile_url": "https://www.linkedin.com/in/jane-doe/",
     "comment": "This hit home."}
  ]
}
```

---

## Commands

| Command | What it does |
|---|---|
| `linkedin import-page --file page.json` | Save a monthly snapshot, build the page dashboard. |
| `linkedin import-event --file event.json` | Save an event, build its dashboard, fold metrics into the episode. |
| `linkedin page-report [period]` | Re-render the page dashboard (latest if no period). |
| `linkedin event-report <key>` | Re-render an event dashboard (key = episode slug / event id / name). |
| `linkedin list` | List imported snapshots and events. |

---

## Privacy

- Commenter and attendee **names live only on your machine** (`data/linkedin/`
  and `data/output/linkedin/`, both git-ignored).
- Only **aggregate, name-free** numbers are committed (the page dashboard in
  `reports/`, and the LinkedIn metrics folded onto episode records).
- If you ever want names committed too, that's a `.gitignore` change — but think
  twice before putting people's names in git history.

## A caution

Automating a personal LinkedIn account (via ConnectSafely or anything else)
carries some risk of LinkedIn restricting the account. Pull at a human cadence
(monthly), don't hammer it, and keep an eye on account health.

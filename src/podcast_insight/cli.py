"""Command-line interface for Podcast Insight.

Run `podcast-insight --help` or `podcast-insight <command> --help` for details.
"""

from __future__ import annotations

import uuid

import click
from rich.console import Console
from rich.table import Table

from . import config, outputs, storage
from .ai.blog_writer import write_blog
from .ai.client import AIClient
from .ai.promo_writer import write_promo
from .ai.social_writer import write_social
from .ai.topic_extractor import extract_topics
from .analytics.apple import AppleConnector
from .analytics.base import NotConfigured
from .analytics.insights import generate_insights
from .analytics.spotify_creators import SpotifyCreatorsConnector
from .analytics.youtube import YouTubeConnector
from .ingest.transcript import build_episode
from .ingest.youtube import build_episode_from_youtube
from .models import Clip

console = Console()


def _note_dry_run(result) -> None:
    if getattr(result, "dry_run", False):
        console.print(
            f"[yellow]Dry-run:[/] no ANTHROPIC_API_KEY set. Prompt written to "
            f"[cyan]{result.prompt_path.relative_to(config.PROJECT_ROOT)}[/]. "
            f"Add a key to .env for automatic output."
        )


@click.group()
@click.version_option(package_name="podcast-insight")
def cli() -> None:
    """Podcast Insight — content + analytics automation for your podcast."""
    config.ensure_dirs()


# ── ingest ───────────────────────────────────────────────────────────────────
@cli.command()
@click.argument("transcript", type=click.Path(exists=True, dir_okay=False))
@click.option("--title", required=True, help="Episode title.")
@click.option("--date", "date_", default=None, help="Air date, YYYY-MM-DD.")
@click.option("--notes", default="", help="Your notes from the episode (optional).")
@click.option("--slug", default=None, help="Override the auto-generated id.")
def ingest(transcript: str, title: str, date_: str | None, notes: str, slug: str | None) -> None:
    """Register an episode from a TRANSCRIPT file."""
    episode = build_episode(transcript, title=title, date=date_, notes=notes, slug=slug)
    path = storage.save(episode)
    console.print(f"[green]Saved[/] episode [bold]{episode.slug}[/] → {path.relative_to(config.PROJECT_ROOT)}")
    console.print(f"Next: [cyan]podcast-insight run {episode.slug}[/]")


# ── topics ───────────────────────────────────────────────────────────────────
@cli.command()
@click.argument("slug")
def topics(slug: str) -> None:
    """Extract & rank the top topics for an episode."""
    episode = storage.load(slug)
    found, result = extract_topics(episode)
    _note_dry_run(result)
    if found:
        episode.topics = found
        storage.save(episode)
        path = outputs.write_topics(episode)
        console.print(f"[green]Extracted {len(found)} topics[/] → {path.relative_to(config.PROJECT_ROOT)}")
        for i, t in enumerate(found, 1):
            console.print(f"  {i}. [bold]{t.title}[/]")


# ── blog ─────────────────────────────────────────────────────────────────────
@cli.command()
@click.argument("slug")
def blog(slug: str) -> None:
    """Write a blog post expanding the top topics, in your voice."""
    episode = storage.load(slug)
    markdown, result = write_blog(episode)
    _note_dry_run(result)
    if markdown:
        episode.blog_markdown = markdown
        storage.save(episode)
        path = outputs.write_blog(episode)
        console.print(f"[green]Blog written[/] → {path.relative_to(config.PROJECT_ROOT)}")


# ── clips ────────────────────────────────────────────────────────────────────
@cli.group()
def clips() -> None:
    """Manage highlight clips for an episode."""


@clips.command("add")
@click.argument("slug")
@click.option("--title", required=True)
@click.option("--start", default=None, help="Start timestamp, e.g. 13:20.")
@click.option("--end", default=None, help="End timestamp, e.g. 16:40.")
@click.option("--note", default="", help="Why this clip matters (helps the copy).")
@click.option("--excerpt", default="", help="Optional transcript text of the clip.")
def clips_add(slug, title, start, end, note, excerpt) -> None:
    """Add a highlight clip to an episode."""
    episode = storage.load(slug)
    clip = Clip(
        id=uuid.uuid4().hex[:8],
        title=title, start=start, end=end, note=note, transcript_excerpt=excerpt,
    )
    episode.clips.append(clip)
    storage.save(episode)
    console.print(f"[green]Added clip[/] [bold]{clip.title}[/] ({clip.id}) to {slug}.")


@clips.command("list")
@click.argument("slug")
def clips_list(slug) -> None:
    """List clips on an episode."""
    episode = storage.load(slug)
    if not episode.clips:
        console.print("No clips yet.")
        return
    for c in episode.clips:
        has = "✓ copy" if c.social else "no copy"
        console.print(f"  [{c.id}] [bold]{c.title}[/] {c.start or '?'}–{c.end or '?'} — {has}")


# ── social ───────────────────────────────────────────────────────────────────
@cli.command()
@click.argument("slug")
def social(slug: str) -> None:
    """Write social media copy for every clip on an episode."""
    episode = storage.load(slug)
    count, results = write_social(episode)
    for r in results:
        if getattr(r, "dry_run", False):
            _note_dry_run(r)
            break
    storage.save(episode)
    path = outputs.write_social(episode)
    console.print(f"[green]Processed {count} clip(s)[/] → {path.relative_to(config.PROJECT_ROOT)}")


# ── run (full pipeline) ──────────────────────────────────────────────────────
@cli.command()
@click.argument("slug")
def run(slug: str) -> None:
    """Run the full content pipeline: topics → blog → social."""
    episode = storage.load(slug)
    client = AIClient()
    if not client.enabled:
        console.print("[yellow]Running in dry-run mode (no API key). Prompts will be written to data/output/prompts/.[/]\n")

    console.rule("[bold]1/3 Topics")
    found, r1 = extract_topics(episode, client)
    _note_dry_run(r1)
    if found:
        episode.topics = found
        storage.save(episode)
        outputs.write_topics(episode)
        for i, t in enumerate(found, 1):
            console.print(f"  {i}. {t.title}")

    console.rule("[bold]2/4 Blog")
    if episode.topics:
        markdown, r2 = write_blog(episode, client)
        _note_dry_run(r2)
        if markdown:
            episode.blog_markdown = markdown
            storage.save(episode)
            outputs.write_blog(episode)
            console.print("  Blog draft written.")
    else:
        console.print("  [dim]Skipped (no topics yet — re-run with an API key).[/]")

    console.rule("[bold]3/4 Blog promo caption")
    if episode.blog_markdown:
        promo, rp = write_promo(episode, client)
        _note_dry_run(rp)
        if promo:
            episode.blog_promo = promo
            storage.save(episode)
            outputs.write_promo(episode)
            console.print(f"  Promo caption written for: {', '.join(promo)}.")
    else:
        console.print("  [dim]Skipped (no blog yet).[/]")

    console.rule("[bold]4/4 Clip social")
    if episode.clips:
        count, results = write_social(episode, client)
        for r in results:
            if getattr(r, "dry_run", False):
                _note_dry_run(r)
                break
        storage.save(episode)
        outputs.write_social(episode)
        console.print(f"  Copy for {count} clip(s) written.")
    else:
        console.print("  [dim]No clips yet. Add some with `clips add` then run `social`.[/]")

    console.rule()
    console.print(f"[green]Done.[/] See [cyan]data/output/[/] for results.")


# ── from-youtube (paste a link → blog + promo caption) ───────────────────────
@cli.command(name="from-youtube")
@click.argument("url")
@click.option("--title", default=None, help="Override the title (else uses YouTube's).")
@click.option("--date", "date_", default=None, help="Air date, YYYY-MM-DD.")
@click.option("--notes", default="", help="Your notes (optional).")
def from_youtube(url: str, title: str | None, date_: str | None, notes: str) -> None:
    """Fetch a YouTube transcript and run topics → blog → promo caption.

    URL can be any YouTube link (watch, youtu.be, live, shorts) or a video id.
    """
    console.print(f"[bold]Fetching transcript from YouTube…[/]")
    try:
        episode = build_episode_from_youtube(url, title=title, date=date_, notes=notes)
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Could not fetch transcript:[/] {exc}")
        raise SystemExit(1)
    storage.save(episode)
    console.print(f"[green]Got it:[/] [bold]{episode.title}[/] ({episode.slug}), "
                  f"{len(episode.transcript.split())} words.\n")

    client = AIClient()
    if not client.enabled:
        console.print("[yellow]Dry-run (no API key) — prompts will be written to data/output/prompts/.[/]\n")

    console.rule("[bold]1/3 Topics")
    found, r1 = extract_topics(episode, client)
    _note_dry_run(r1)
    if found:
        episode.topics = found
        storage.save(episode)
        outputs.write_topics(episode)
        for i, t in enumerate(found, 1):
            console.print(f"  {i}. {t.title}")

    console.rule("[bold]2/3 Blog")
    if episode.topics:
        markdown, r2 = write_blog(episode, client)
        _note_dry_run(r2)
        if markdown:
            episode.blog_markdown = markdown
            storage.save(episode)
            outputs.write_blog(episode)
            console.print("  Blog draft written.")

    console.rule("[bold]3/3 Blog promo caption")
    if episode.blog_markdown:
        promo, rp = write_promo(episode, client)
        _note_dry_run(rp)
        if promo:
            episode.blog_promo = promo
            storage.save(episode)
            outputs.write_promo(episode)
            console.print(f"  Promo caption written for: {', '.join(promo)}.")

    console.rule()
    console.print(f"[green]Done.[/] See [cyan]data/output/[/]. "
                  f"Commit the new episode so the monthly analytics job can track it.")


# ── promo (blog caption only) ────────────────────────────────────────────────
@cli.command()
@click.argument("slug")
def promo(slug: str) -> None:
    """Write a social caption promoting the blog post."""
    episode = storage.load(slug)
    captions, result = write_promo(episode)
    _note_dry_run(result)
    if captions:
        episode.blog_promo = captions
        storage.save(episode)
        path = outputs.write_promo(episode)
        console.print(f"[green]Promo caption written[/] → {path.relative_to(config.PROJECT_ROOT)}")


# ── auth (one-time OAuth setup) ──────────────────────────────────────────────
@cli.group()
def auth() -> None:
    """One-time authentication setup for analytics connectors."""


@auth.command("youtube")
@click.option("--client-secret", "client_secret", default=None,
              help="Path to your OAuth client-secret JSON (else uses YOUTUBE_OAUTH_CLIENT_SECRET_FILE).")
def auth_youtube(client_secret: str | None) -> None:
    """Run the one-time YouTube Analytics OAuth consent and save a token."""
    from .analytics.youtube_oauth import run_oauth_flow

    secret_file = client_secret or config.env("YOUTUBE_OAUTH_CLIENT_SECRET_FILE")
    if not secret_file:
        console.print("[red]Need a client-secret JSON.[/] Pass --client-secret or set "
                      "YOUTUBE_OAUTH_CLIENT_SECRET_FILE in .env. See docs/CONNECTING_ANALYTICS.md.")
        raise SystemExit(1)
    refresh_token = run_oauth_flow(secret_file)
    console.print("[green]Authorized.[/] Token saved locally.")
    if refresh_token:
        console.print("\nFor the cloud (GitHub Actions) job, store these as secrets:")
        console.print("  YOUTUBE_OAUTH_REFRESH_TOKEN = [bold](shown below)[/]")
        console.print(f"\n[cyan]{refresh_token}[/]\n")
        console.print("(Also store YOUTUBE_OAUTH_CLIENT_ID and YOUTUBE_OAUTH_CLIENT_SECRET.)")


# ── set platform ids ─────────────────────────────────────────────────────────
@cli.command("set")
@click.argument("slug")
@click.option("--youtube", "youtube_id", default=None, help="YouTube video id.")
@click.option("--spotify", "spotify_id", default=None, help="Spotify episode id.")
@click.option("--apple-title", default=None, help="Title as it appears in Apple exports.")
def set_ids(slug, youtube_id, spotify_id, apple_title) -> None:
    """Attach platform ids to an episode (needed for analytics)."""
    episode = storage.load(slug)
    if youtube_id:
        episode.youtube_video_id = youtube_id
    if spotify_id:
        episode.spotify_episode_id = spotify_id
    if apple_title:
        episode.apple_episode_title = apple_title
    storage.save(episode)
    console.print(f"[green]Updated[/] platform ids for {slug}.")


# ── analytics ────────────────────────────────────────────────────────────────
@cli.group()
def analytics() -> None:
    """Pull performance data from platforms."""


_CONNECTORS = {
    "youtube": YouTubeConnector,
    "spotify": SpotifyCreatorsConnector,
    "apple": AppleConnector,
}


def _pull_episode(episode, quiet: bool = False) -> int:
    """Pull all configured platforms for one episode. Returns records added."""
    enabled = config.settings().get("analytics", {}).get("platforms", [])
    new_records = []
    for name in enabled:
        ctor = _CONNECTORS.get(name)
        if not ctor:
            continue
        try:
            record = ctor().fetch(episode)
            if record:
                new_records.append(record)
                if not quiet:
                    console.print(f"[green]{name}:[/] pulled.")
            elif not quiet:
                console.print(f"[yellow]{name}:[/] no data returned.")
        except NotConfigured as exc:
            if not quiet:
                console.print(f"[dim]{name}: skipped — {exc}[/]")
        except Exception as exc:  # noqa: BLE001
            console.print(f"[red]{name}: error — {exc}[/]")
    if new_records:
        episode.analytics.extend(new_records)
        storage.save(episode)
    return len(new_records)


@analytics.command("pull")
@click.argument("slug")
def analytics_pull(slug: str) -> None:
    """Pull analytics for one episode from configured platforms."""
    episode = storage.load(slug)
    added = _pull_episode(episode)
    console.print(f"[green]Saved {added} record(s).[/]" if added else "[yellow]No records saved.[/]")


@analytics.command("pull-all")
def analytics_pull_all() -> None:
    """Pull analytics for EVERY episode (used by the monthly job)."""
    episodes = storage.all_episodes()
    if not episodes:
        console.print("No episodes found.")
        return
    total = 0
    for ep in episodes:
        console.print(f"[bold]{ep.slug}[/]")
        total += _pull_episode(ep)
    console.print(f"\n[green]Done. {total} record(s) across {len(episodes)} episode(s).[/]")


@cli.command()
@click.option("--stamp", default=None, help="Label for the saved report, e.g. 2026-06.")
def insights(stamp: str | None) -> None:
    """Rank top performers and generate recommendations across all episodes."""
    episodes = storage.all_episodes()
    if not episodes:
        console.print("No episodes yet. Ingest some first.")
        return
    markdown, scores, result = generate_insights(episodes)

    table = Table(title="Episode ranking (combined score)")
    table.add_column("#", justify="right")
    table.add_column("Episode")
    table.add_column("Score", justify="right")
    for i, s in enumerate(scores, 1):
        table.add_row(str(i), s.title, f"{s.score:.3f}")
    console.print(table)

    _note_dry_run(result)
    if markdown:
        outputs.write_insights(markdown, stamp=stamp)
        console.print(f"[green]Insights written[/] → reports/insights-latest.md")


# ── list ─────────────────────────────────────────────────────────────────────
@cli.command(name="list")
def list_episodes() -> None:
    """Show all episodes and what's been generated for each."""
    episodes = storage.all_episodes()
    if not episodes:
        console.print("No episodes yet. Try: [cyan]podcast-insight ingest examples/sample_episode.md --title \"...\"[/]")
        return
    table = Table()
    table.add_column("Slug")
    table.add_column("Title")
    table.add_column("Date")
    table.add_column("Topics", justify="right")
    table.add_column("Blog")
    table.add_column("Clips", justify="right")
    table.add_column("Analytics", justify="right")
    for e in episodes:
        table.add_row(
            e.slug, e.title, e.date.isoformat() if e.date else "—",
            str(len(e.topics)), "✓" if e.blog_markdown else "—",
            str(len(e.clips)), str(len(e.analytics)),
        )
    console.print(table)


if __name__ == "__main__":
    cli()

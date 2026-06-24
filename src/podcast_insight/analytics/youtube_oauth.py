"""Official YouTube Analytics API access via OAuth (free, sanctioned).

This is the channel-owner-only data: estimated watch time, average view
duration, and subscribers gained. It needs a one-time OAuth consent, after which
a refresh token lets it run unattended forever (including in GitHub Actions).

Two ways credentials are loaded, in priority order:
  1. Environment variables (best for CI / GitHub Actions):
       YOUTUBE_OAUTH_CLIENT_ID
       YOUTUBE_OAUTH_CLIENT_SECRET
       YOUTUBE_OAUTH_REFRESH_TOKEN
  2. A token file written by `podcast-insight auth youtube` (best for local):
       YOUTUBE_OAUTH_TOKEN_FILE  (default: secrets/youtube_token.json)

If none are present, callers get NotConfigured and skip private metrics (public
stats still work with just YOUTUBE_API_KEY).
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Optional

from .. import config
from .base import NotConfigured

SCOPES = ["https://www.googleapis.com/auth/yt-analytics.readonly"]
DEFAULT_TOKEN_FILE = "secrets/youtube_token.json"
TOKEN_URI = "https://oauth2.googleapis.com/token"


def _token_file() -> Path:
    rel = config.env("YOUTUBE_OAUTH_TOKEN_FILE", DEFAULT_TOKEN_FILE)
    return (config.PROJECT_ROOT / rel).resolve()


def _require_google():
    try:
        from google.oauth2.credentials import Credentials  # noqa: F401
        from googleapiclient.discovery import build  # noqa: F401
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "Google libraries not installed. Run: pip install -e '.[analytics]'"
        ) from exc


def load_credentials():
    """Return refreshable Credentials, or raise NotConfigured."""
    _require_google()
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    client_id = config.env("YOUTUBE_OAUTH_CLIENT_ID")
    client_secret = config.env("YOUTUBE_OAUTH_CLIENT_SECRET")
    refresh_token = config.env("YOUTUBE_OAUTH_REFRESH_TOKEN")

    creds = None
    if client_id and client_secret and refresh_token:
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            token_uri=TOKEN_URI,
            scopes=SCOPES,
        )
    else:
        tf = _token_file()
        if tf.exists():
            creds = Credentials.from_authorized_user_file(str(tf), SCOPES)

    if not creds:
        raise NotConfigured(
            "YouTube Analytics OAuth not set up. Run `podcast-insight auth youtube` "
            "once, or set YOUTUBE_OAUTH_CLIENT_ID/SECRET/REFRESH_TOKEN "
            "(see docs/CONNECTING_ANALYTICS.md)."
        )
    if not creds.valid:
        creds.refresh(Request())
    return creds


def fetch_video_metrics(video_id: str) -> Optional[dict]:
    """Query lifetime private metrics for one video. Returns a dict or None."""
    from googleapiclient.discovery import build

    creds = load_credentials()
    service = build("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)
    resp = service.reports().query(
        ids="channel==MINE",
        startDate="2005-02-14",  # before YouTube existed = "all time"
        endDate=date.today().isoformat(),
        metrics="estimatedMinutesWatched,averageViewDuration,views,subscribersGained",
        filters=f"video=={video_id}",
    ).execute()

    rows = resp.get("rows") or []
    if not rows:
        return None
    headers = [h["name"] for h in resp.get("columnHeaders", [])]
    return dict(zip(headers, rows[0]))


def run_oauth_flow(client_secret_file: str) -> str:
    """One-time interactive consent. Saves a token file and returns the refresh
    token (so you can store it as a GitHub Actions secret for the cloud job)."""
    _require_google()
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
    creds = flow.run_local_server(port=0)

    tf = _token_file()
    tf.parent.mkdir(parents=True, exist_ok=True)
    tf.write_text(creds.to_json(), encoding="utf-8")
    return creds.refresh_token or ""

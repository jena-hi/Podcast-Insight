"""Apple Podcasts connector.

Apple Podcasts Connect has no open public analytics API. The supported path is to
download a CSV export from Apple Podcasts Connect and drop it in a folder; this
connector reads the latest export and matches rows to episodes by title.

This is implemented defensively: it looks for any CSV in APPLE_PODCASTS_EXPORT_DIR
and tries to find plays/listeners columns by common header names. If Apple changes
the format, adjust COLUMN_ALIASES below.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import Optional

from .. import config
from ..models import AnalyticsRecord, Episode
from .base import NotConfigured

# Map our fields -> the header names Apple might use (lowercased, matched loosely).
COLUMN_ALIASES = {
    "title": ["title", "episode", "episode title", "name"],
    "listens": ["plays", "listens", "streams", "total plays"],
    "listeners": ["listeners", "unique listeners"],
    "engaged": ["engaged plays", "engaged listeners"],
}


class AppleConnector:
    name = "apple"

    def __init__(self) -> None:
        export_dir = config.env("APPLE_PODCASTS_EXPORT_DIR", "data/analytics/apple_exports")
        self.export_dir = (config.PROJECT_ROOT / export_dir).resolve()

    def _latest_csv(self) -> Path:
        if not self.export_dir.exists():
            raise NotConfigured(
                f"No Apple export folder at {self.export_dir}. Download a CSV from "
                f"Apple Podcasts Connect and put it there "
                f"(see docs/CONNECTING_ANALYTICS.md)."
            )
        csvs = sorted(self.export_dir.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not csvs:
            raise NotConfigured(f"No .csv files found in {self.export_dir}.")
        return csvs[0]

    def fetch(self, episode: Episode) -> Optional[AnalyticsRecord]:
        path = self._latest_csv()
        match_title = (episode.apple_episode_title or episode.title).strip().lower()

        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            headers = {h.lower().strip(): h for h in (reader.fieldnames or [])}
            cols = {field: _find(headers, names) for field, names in COLUMN_ALIASES.items()}
            if not cols["title"]:
                raise NotConfigured(
                    f"Couldn't find a title column in {path.name}. "
                    f"Headers were: {list(headers.values())}"
                )
            for row in reader:
                if str(row.get(cols["title"], "")).strip().lower() == match_title:
                    return AnalyticsRecord(
                        platform=self.name,
                        pulled_on=date.today(),
                        listens=_int(row.get(cols["listens"])) if cols["listens"] else None,
                        extra=_extra(row, cols),
                    )
        return None  # episode not found in the export


def _find(headers: dict[str, str], names: list[str]) -> Optional[str]:
    for n in names:
        if n in headers:
            return headers[n]
    return None


def _int(value) -> Optional[int]:
    try:
        return int(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _extra(row: dict, cols: dict) -> dict[str, float]:
    out: dict[str, float] = {}
    for field in ("listeners", "engaged"):
        col = cols.get(field)
        if col and (val := _int(row.get(col))) is not None:
            out[field] = float(val)
    return out

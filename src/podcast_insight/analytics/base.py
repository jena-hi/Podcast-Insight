"""Shared pieces for analytics connectors.

Each connector implements `fetch(episode) -> AnalyticsRecord | None`. If it isn't
configured (missing keys), it raises NotConfigured so the caller can skip it with
a friendly message instead of crashing.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional, Protocol

from ..models import AnalyticsRecord, Episode


class NotConfigured(Exception):
    """Raised when a connector lacks the credentials/ids it needs."""


class Connector(Protocol):
    name: str

    def fetch(self, episode: Episode) -> Optional[AnalyticsRecord]:
        ...


def http_get_json(url: str, params: dict[str, Any] | None = None,
                  headers: dict[str, str] | None = None) -> dict[str, Any]:
    """Minimal JSON GET using the standard library (no extra dependencies)."""
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 — known APIs
        return json.loads(resp.read().decode("utf-8"))


def http_post_form(url: str, data: dict[str, Any],
                   headers: dict[str, str] | None = None) -> dict[str, Any]:
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers or {})
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))

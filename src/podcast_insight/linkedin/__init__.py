"""LinkedIn analytics layer: monthly Page stats + per-event dashboards.

Data is sourced via the ConnectSafely connector inside a Claude session (see
CLAUDE.md and docs/LINKEDIN.md). This package is source-agnostic: it stores and
renders whatever structured data it's given, so it also works from a manual paste.

Privacy: attendee and commenter NAMES are personal data and are kept LOCAL ONLY
(under data/linkedin/, which is git-ignored). Only aggregate, name-free metrics
are written to the git-tracked reports/ folder.
"""

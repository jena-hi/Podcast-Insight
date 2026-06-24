"""Auto-publishing hooks (stubs).

These are intentionally NOT wired up. Publishing is the riskiest part to automate
(platform rate limits, review policies, irreversible posts), so the design keeps
it opt-in and separate. When you're ready, implement these and call them from the
CLI behind an explicit `--publish` flag.

See docs/AUTOMATION.md for the recommended order to enable them.
"""

"""Project links shown in the landing footer. Configure with environment variables; nothing is invented.

    SLOTSMITH_REPO_URL, SLOTSMITH_DOCS_URL, SLOTSMITH_VIDEO_URL   (https:// URLs only)
"""
from __future__ import annotations

import os

LINKS = [("Repository", "SLOTSMITH_REPO_URL"), ("Documentation", "SLOTSMITH_DOCS_URL"), ("Demo video", "SLOTSMITH_VIDEO_URL")]


def configured_links(env=None) -> list[tuple[str, str | None]]:
    """(label, url) for each known link; url is None when the variable is unset or not an https URL."""
    env = os.environ if env is None else env
    out = []
    for label, var in LINKS:
        url = (env.get(var) or "").strip()
        out.append((label, url if url.startswith("https://") and " " not in url else None))
    return out

"""Persistence helpers for editable superuser roadmap content."""
from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data"
FUTURE_UPDATES_FILE = DATA_DIR / "future_updates.json"

DEFAULT_FUTURE_UPDATES = [
    {
        "id": "hot-topics-publishing",
        "title": "Hot topics publishing",
        "phase": "Next up",
        "description": "Move hot topic reports into the same upload, review, approve, and publish flow as the core collections.",
        "items": [
            "Upload hot topic source files or structured JSON",
            "Generate summaries and charts through the review flow",
            "Publish reports directly into the public hot topics section",
        ],
    },
    {
        "id": "debt-schedules",
        "title": "Debt schedules and deeper finance rows",
        "phase": "Planned",
        "description": "Extend published finance records so repayment schedules and deeper debt tables no longer rely on fallback data.",
        "items": [
            "Add repayment schedule rows to the publish layer",
            "Surface creditor schedule updates on the public debt page",
            "Keep one live source of truth for uploaded finance records",
        ],
    },
    {
        "id": "homepage-modules",
        "title": "Homepage content modules",
        "phase": "Planned",
        "description": "Bring remaining editorial homepage blocks into a managed data flow where it makes sense.",
        "items": [
            "Decide which homepage blocks stay editorial",
            "Move eligible sections into collection-based publishing",
            "Keep non-dynamic content clearly separated from published data",
        ],
    },
    {
        "id": "release-controls",
        "title": "Smarter release controls",
        "phase": "Later",
        "description": "Add stronger publishing controls so approved data can be scheduled, versioned, and rolled back cleanly.",
        "items": [
            "Scheduled publish windows",
            "Version history and superseded document tracking",
            "Rollback support for live public datasets",
        ],
    },
    {
        "id": "collection-expansion",
        "title": "Collection expansion",
        "phase": "Later",
        "description": "Add more specialized collections only after the current ones feel stable and easy for operators to manage.",
        "items": [
            "Additional public accountability content",
            "Sector-specific uploads beyond finance and health",
            "More structured data templates for repeatable reporting",
        ],
    },
]


def _ensure_file() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not FUTURE_UPDATES_FILE.exists():
        FUTURE_UPDATES_FILE.write_text(
            json.dumps(DEFAULT_FUTURE_UPDATES, indent=2),
            encoding="utf-8",
        )


def load_future_updates() -> list[dict]:
    """Load roadmap cards from disk, creating defaults if needed."""
    _ensure_file()
    try:
        raw = json.loads(FUTURE_UPDATES_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        save_future_updates(DEFAULT_FUTURE_UPDATES)
        return [*DEFAULT_FUTURE_UPDATES]

    if not isinstance(raw, list):
        save_future_updates(DEFAULT_FUTURE_UPDATES)
        return [*DEFAULT_FUTURE_UPDATES]

    return raw


def save_future_updates(items: list[dict]) -> None:
    """Persist roadmap cards to disk."""
    _ensure_file()
    FUTURE_UPDATES_FILE.write_text(json.dumps(items, indent=2), encoding="utf-8")

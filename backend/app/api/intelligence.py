"""Read-only Intelligence imprint API (JSON-on-disk, Issue 01).

Raises HTTP 404 when snapshot data is unavailable — never mocks empty payloads.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query

from app.services.document_ingestion import INTELLIGENCE_DATA_DIR, REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ingestion.intelligence.capture.registry import load_registry  # noqa: E402
from ingestion.intelligence.cohort import load_cohort_file  # noqa: E402

router = APIRouter()


def _processed_dir() -> Path:
    return INTELLIGENCE_DATA_DIR / "processed"


def _latest_capture_date() -> Optional[date]:
    """Prefer the newest registry capture_date that has a processed directory."""
    registry = load_registry()
    dates = sorted({record.capture_date for record in registry.captures}, reverse=True)
    for capture_date in dates:
        folder = _processed_dir() / capture_date.isoformat()
        if folder.is_dir() and any(folder.glob("*.json")):
            return capture_date
    # Fall back to on-disk processed folders (may predate registry).
    if not _processed_dir().exists():
        return None
    disk_dates = sorted(
        (p.name for p in _processed_dir().iterdir() if p.is_dir()),
        reverse=True,
    )
    for name in disk_dates:
        try:
            return date.fromisoformat(name)
        except ValueError:
            continue
    return None


def _load_processed(bank_id: str, capture_date: date) -> dict[str, Any]:
    path = _processed_dir() / capture_date.isoformat() / f"{bank_id}.json"
    if not path.exists():
        raise FileNotFoundError(str(path))
    return json.loads(path.read_text(encoding="utf-8"))


def _followers_for(platform: str, payload: dict[str, Any]) -> Optional[int]:
    for metric in payload.get("social_metrics") or []:
        if metric.get("platform") != platform:
            continue
        if (metric.get("source") or {}).get("method") == "wayback":
            continue
        followers = metric.get("followers")
        if followers is not None:
            return int(followers)
    return None


def _pagespeed(payload: dict[str, Any]) -> Optional[dict[str, Any]]:
    for metric in payload.get("web_metrics") or []:
        source = metric.get("source") or {}
        if source.get("method") != "api":
            continue
        labels = metric.get("top_keywords") or []
        if not any(str(label).startswith("performance:") for label in labels):
            continue
        scores: dict[str, int] = {}
        for label in labels:
            if ":" not in str(label):
                continue
            key, raw = str(label).split(":", 1)
            try:
                scores[key] = int(raw)
            except ValueError:
                continue
        return {
            "performance": metric.get("authority_score"),
            "categories": scores,
            "source_url": source.get("url"),
        }
    return None


def build_snapshot(capture_date: date) -> dict[str, Any]:
    """Assemble cohort snapshot for one capture date from processed JSON."""
    cohort = load_cohort_file()
    banks: list[dict[str, Any]] = []
    missing: list[str] = []

    for entry in cohort.cohort:
        try:
            payload = _load_processed(entry.id, capture_date)
        except FileNotFoundError:
            missing.append(entry.id)
            continue

        banks.append(
            {
                "bank_id": entry.id,
                "display_name": entry.display_name,
                "short_name": entry.short_name,
                "series_token": entry.series_token,
                "domain": entry.domain,
                "facebook_followers": _followers_for("facebook", payload),
                "instagram_followers": _followers_for("instagram", payload),
                "youtube_subscribers": _followers_for("youtube", payload),
                "twitter_followers": _followers_for("twitter", payload),
                "pagespeed": _pagespeed(payload),
                "errors": payload.get("errors") or [],
                "processed_path": str(
                    (
                        Path("data")
                        / "intelligence"
                        / "processed"
                        / capture_date.isoformat()
                        / f"{entry.id}.json"
                    )
                ),
            }
        )

    if not banks:
        raise FileNotFoundError(
            f"No processed intelligence captures for {capture_date.isoformat()}"
        )

    confirmed = {
        "facebook": sum(1 for b in banks if b["facebook_followers"] is not None),
        "instagram": sum(1 for b in banks if b["instagram_followers"] is not None),
        "youtube": sum(1 for b in banks if b["youtube_subscribers"] is not None),
        "pagespeed": sum(1 for b in banks if b["pagespeed"] is not None),
    }

    return {
        "imprint": "Bahamas Open Data | Intelligence",
        "edition": "Banking Sector 2026",
        "capture_date": capture_date.isoformat(),
        "measurement_window": {
            "start": "2025-10-01",
            "end": "2026-09-30",
            "timezone": "America/Nassau",
        },
        "thin_data_note": (
            "Bahamian digital footprints are sparse. Confirmed public signals are "
            "shown; missing platforms stay null — never invented."
        ),
        "confirmed_bank_counts": confirmed,
        "banks": banks,
        "missing_banks": missing,
        "methodology_path": "ingestion/intelligence/methodology.md",
        "repo_root": str(REPO_ROOT),
    }


@router.get("/snapshot")
async def intelligence_snapshot(
    capture_date: Optional[str] = Query(
        default=None,
        description="YYYY-MM-DD; defaults to latest registry/processed date",
    ),
):
    """Return the cohort intelligence snapshot for a capture date."""
    if capture_date:
        try:
            resolved = date.fromisoformat(capture_date)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid capture_date") from exc
    else:
        resolved = _latest_capture_date()
        if resolved is None:
            raise HTTPException(
                status_code=404,
                detail="No intelligence captures available on disk",
            )

    try:
        return build_snapshot(resolved)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

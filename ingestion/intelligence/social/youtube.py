"""YouTube channel metrics via YouTube Data API v3 (free quota).

Resolves cohort ``social.youtube`` values that are either:
  - a handle (``@RBC`` or ``RBC``) via ``channels.list?forHandle=``
  - a channel id (``UC…``) via ``channels.list?id=``

Subscriber / view counts come from ``statistics``. Hidden subscriber
counts yield ``followers=None`` (never inferred). Requires
``YOUTUBE_API_KEY`` in the environment / settings.
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlencode

import httpx

from backend.app.services.document_ingestion import INTELLIGENCE_DATA_DIR, REPO_ROOT
from ingestion.intelligence.cohort import CohortEntry, get_user_agent
from ingestion.intelligence.errors import CaptureError
from ingestion.intelligence.types import (
    CaptureResult,
    Platform,
    SocialMetric,
    SourceProvenance,
)

YOUTUBE_API = "https://www.googleapis.com/youtube/v3/channels"
_CHANNEL_ID_PREFIX = "UC"
_CHANNEL_ID_LENGTH = 24


def _get_api_key() -> str:
    """Return the YouTube Data API key from settings or the environment."""
    try:
        from backend.app.core.config import settings

        key = (getattr(settings, "YOUTUBE_API_KEY", None) or "").strip()
        if key:
            return key
    except Exception:
        pass
    return os.getenv("YOUTUBE_API_KEY", "").strip()


def _is_channel_id(value: str) -> bool:
    return value.startswith(_CHANNEL_ID_PREFIX) and len(value) == _CHANNEL_ID_LENGTH


def resolve_channel_lookup(handle: str) -> dict[str, str]:
    """Map a cohort youtube value to channels.list query params (sans key/part)."""
    value = handle.strip()
    if not value:
        raise ValueError("empty youtube handle")
    if _is_channel_id(value):
        return {"id": value}
    return {"forHandle": value.lstrip("@")}


def public_channel_url(handle: str) -> str:
    """Canonical public URL for provenance (not the API endpoint)."""
    value = handle.strip()
    if _is_channel_id(value):
        return f"https://www.youtube.com/channel/{value}"
    normalized = value if value.startswith("@") else f"@{value.lstrip('@')}"
    return f"https://www.youtube.com/{normalized}"


def _parse_int(raw: Any) -> Optional[int]:
    if raw is None:
        return None
    try:
        parsed = int(raw)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def parse_channel_statistics(payload: dict[str, Any]) -> tuple[Optional[int], Optional[int], list[str]]:
    """Extract (followers, views) from a channels.list JSON body.

    Returns soft-error strings when the channel is missing or subscribers are hidden.
    """
    errors: list[str] = []
    items = payload.get("items") or []
    if not items:
        errors.append("youtube: channel not found in API response")
        return None, None, errors

    statistics = items[0].get("statistics") or {}
    views = _parse_int(statistics.get("viewCount"))

    if statistics.get("hiddenSubscriberCount") is True:
        errors.append("youtube: subscriber count hidden by channel")
        return None, views, errors

    followers = _parse_int(statistics.get("subscriberCount"))
    if followers is None and "subscriberCount" not in statistics:
        errors.append("youtube: subscriberCount missing from statistics")
    return followers, views, errors


def _raw_artifact_path(bank_id: str, capture_date: date) -> Path:
    return (
        INTELLIGENCE_DATA_DIR
        / "raw"
        / capture_date.isoformat()
        / bank_id
        / "youtube_channel.json"
    )


def _quota_or_auth_error(status_code: int, body: str) -> bool:
    if status_code in {401, 403}:
        return True
    if status_code == 429:
        return True
    lowered = body.lower()
    return any(
        token in lowered
        for token in ("quotaexceeded", "ratelimitexceeded", "accessnotconfigured")
    )


async def _fetch_channel(
    client: httpx.AsyncClient,
    api_key: str,
    lookup: dict[str, str],
) -> tuple[dict[str, Any], int, str]:
    """Call channels.list; return (json, http_status, request_url)."""
    params = {
        "part": "snippet,statistics",
        "key": api_key,
        **lookup,
    }
    request_url = f"{YOUTUBE_API}?{urlencode(params)}"
    response = await client.get(YOUTUBE_API, params=params)
    body_text = response.text
    if _quota_or_auth_error(response.status_code, body_text):
        raise CaptureError(
            f"YouTube API rate-limited, unauthorized, or unavailable "
            f"({response.status_code})"
        )
    if response.status_code >= 400:
        raise CaptureError(
            f"YouTube API HTTP {response.status_code}: {body_text[:200]}"
        )
    try:
        payload = response.json()
    except ValueError as exc:
        raise CaptureError(f"YouTube API returned non-JSON body: {exc}") from exc
    return payload, response.status_code, request_url


async def capture(
    bank_id: str,
    cohort_entry: CohortEntry,
    capture_date: date,
) -> CaptureResult:
    """
    Pull public channel statistics for the bank's configured YouTube handle.

    Returns CaptureResult with at most one SocialMetric. Raises CaptureError on
    rate-limit / auth / hard API failures — never substitutes synthetic counts.
    """
    handle = (cohort_entry.social.youtube or "").strip()
    if not handle:
        return CaptureResult(
            bank_id=bank_id,
            capture_date=capture_date,
            attempted_platforms=[],
            errors=["youtube: no handle configured for this bank"],
        )

    api_key = _get_api_key()
    if not api_key:
        raise CaptureError("YOUTUBE_API_KEY is not set")

    attempted_platforms = [Platform.YOUTUBE]
    errors: list[str] = []
    social_metrics: list[SocialMetric] = []
    raw_artifacts: dict[str, str] = {}
    fetched_at = datetime.now(timezone.utc)

    try:
        lookup = resolve_channel_lookup(handle)
    except ValueError as exc:
        return CaptureResult(
            bank_id=bank_id,
            capture_date=capture_date,
            attempted_platforms=attempted_platforms,
            errors=[f"youtube: {exc}"],
        )

    headers = {"User-Agent": get_user_agent()}
    async with httpx.AsyncClient(headers=headers, timeout=60.0) as client:
        try:
            payload, http_status, _request_url = await _fetch_channel(
                client, api_key, lookup
            )
        except CaptureError:
            raise
        except httpx.HTTPError as exc:
            raise CaptureError(f"YouTube API HTTP error: {exc}") from exc

    artifact_path = _raw_artifact_path(bank_id, capture_date)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    raw_artifacts["youtube_channel"] = str(artifact_path.relative_to(REPO_ROOT))

    followers, views, parse_errors = parse_channel_statistics(payload)
    errors.extend(parse_errors)

    # Record a metric row whenever the API returned a channel item, even if
    # followers are hidden/None — preserves provenance for audit.
    items = payload.get("items") or []
    if items:
        social_metrics.append(
            SocialMetric(
                bank_id=bank_id,
                platform=Platform.YOUTUBE,
                capture_date=capture_date,
                followers=followers,
                views=views,
                source=SourceProvenance(
                    url=public_channel_url(handle),
                    fetched_at=fetched_at,
                    http_status=http_status,
                    method="api",
                ),
            )
        )

    return CaptureResult(
        bank_id=bank_id,
        capture_date=capture_date,
        social_metrics=social_metrics,
        raw_artifacts=raw_artifacts,
        errors=errors,
        attempted_platforms=attempted_platforms,
    )

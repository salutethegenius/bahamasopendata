"""Historical follower counts via archive.org (Wayback Machine).

CDX matching uses the nearest snapshot within ±7 days of ``capture_date``
(one row per calendar day via ``collapse=timestamp:8``). The actual snapshot
date is preserved in ``SourceProvenance.archive_url`` — we never re-date
artifacts to ``capture_date``.

Follower parsing is implemented for Facebook, Instagram, and Twitter HTML
only. YouTube and TikTok Wayback captures rarely expose follower counts in
static HTML; those platforms are handled by dedicated scrapers (e.g.
Social Blade). LinkedIn seeds are accepted but typically yield
``followers=None`` unless a parseable count appears in the archive.
"""
from __future__ import annotations

import asyncio
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx

from backend.app.services.document_ingestion import INTELLIGENCE_DATA_DIR, REPO_ROOT
from ingestion.intelligence.cohort import CohortEntry, get_rate_limit_seconds, get_user_agent
from ingestion.intelligence.errors import CaptureError
from ingestion.intelligence.types import (
    CaptureResult,
    Platform,
    SocialMetric,
    SourceProvenance,
)

CDX_API = "https://web.archive.org/cdx/search/cdx"
ARCHIVE_BASE = "https://web.archive.org/web"
CDX_WINDOW_DAYS = 7

_WAYBACK_ATTEMPTED_PLATFORMS = frozenset(
    {Platform.FACEBOOK, Platform.INSTAGRAM, Platform.TWITTER}
)


def _attempted_platforms_from_seeds(seeds: list[str]) -> list[Platform]:
    """Return FB/IG/Twitter platforms with a usable wayback seed URL in the cohort."""
    seen: set[Platform] = set()
    attempted: list[Platform] = []
    for seed_url in seeds:
        platform = _platform_for_url(seed_url)
        if platform in _WAYBACK_ATTEMPTED_PLATFORMS and platform not in seen:
            seen.add(platform)
            attempted.append(platform)
    return attempted


_FOLLOWER_PATTERNS: dict[Platform, re.Pattern[str]] = {
    Platform.FACEBOOK: re.compile(
        r"([\d,.]+[KMB]?)\s+followers",
        re.IGNORECASE,
    ),
    Platform.INSTAGRAM: re.compile(
        r"([\d,.]+[KMB]?)\s+followers",
        re.IGNORECASE,
    ),
    Platform.TWITTER: re.compile(
        r"([\d,.]+[KMB]?)\s+followers",
        re.IGNORECASE,
    ),
}


def _platform_for_url(url: str) -> Optional[Platform]:
    host = urlparse(url).netloc.lower()
    if "facebook.com" in host:
        return Platform.FACEBOOK
    if "instagram.com" in host:
        return Platform.INSTAGRAM
    if "twitter.com" in host or "x.com" in host:
        return Platform.TWITTER
    if "youtube.com" in host:
        return Platform.YOUTUBE
    if "tiktok.com" in host:
        return Platform.TIKTOK
    if "linkedin.com" in host:
        return Platform.LINKEDIN
    return None


def _parse_follower_count(text: str, platform: Platform) -> Optional[int]:
    pattern = _FOLLOWER_PATTERNS.get(platform)
    if not pattern:
        return None
    match = pattern.search(text)
    if not match:
        return None
    raw = match.group(1).replace(",", "").strip().upper()
    multiplier = 1
    if raw.endswith("K"):
        multiplier = 1_000
        raw = raw[:-1]
    elif raw.endswith("M"):
        multiplier = 1_000_000
        raw = raw[:-1]
    elif raw.endswith("B"):
        multiplier = 1_000_000_000
        raw = raw[:-1]
    try:
        return int(float(raw) * multiplier)
    except ValueError:
        return None


def _cdx_window_bounds(capture_date: date) -> tuple[str, str]:
    """Return CDX ``from`` and ``to`` bounds (YYYYMMDD) for the ±window."""
    start = capture_date - timedelta(days=CDX_WINDOW_DAYS)
    end = capture_date + timedelta(days=CDX_WINDOW_DAYS)
    return start.strftime("%Y%m%d"), end.strftime("%Y%m%d")


def _snapshot_date_from_timestamp(timestamp: str) -> date:
    """Parse YYYYMMDD from a Wayback timestamp string."""
    return date(int(timestamp[0:4]), int(timestamp[4:6]), int(timestamp[6:8]))


def _pick_nearest_cdx_timestamp(rows: list, capture_date: date) -> Optional[str]:
    """Select the CDX row whose snapshot date is closest to capture_date."""
    if len(rows) < 2:
        return None

    best_timestamp: Optional[str] = None
    best_distance: Optional[int] = None

    for row in rows[1:]:
        if len(row) < 2:
            continue
        timestamp = row[1]
        if not timestamp or len(timestamp) < 8:
            continue
        snapshot_date = _snapshot_date_from_timestamp(timestamp)
        distance = abs((snapshot_date - capture_date).days)
        if best_distance is None or distance < best_distance:
            best_distance = distance
            best_timestamp = timestamp

    return best_timestamp


_CDX_RETRIES = 3
_CDX_RETRY_SLEEP_SECONDS = 45.0


async def _fetch_cdx_timestamp(
    client: httpx.AsyncClient,
    seed_url: str,
    capture_date: date,
) -> Optional[str]:
    """Return the nearest Wayback timestamp within ±CDX_WINDOW_DAYS of capture_date."""
    from_date, to_date = _cdx_window_bounds(capture_date)
    params = {
        "url": seed_url,
        "from": from_date,
        "to": to_date,
        "output": "json",
        "filter": "statuscode:200",
        "collapse": "timestamp:8",
    }
    last_status = 0
    for attempt in range(1, _CDX_RETRIES + 1):
        response = await client.get(CDX_API, params=params)
        last_status = response.status_code
        if response.status_code in {429, 503}:
            if attempt < _CDX_RETRIES:
                await asyncio.sleep(_CDX_RETRY_SLEEP_SECONDS * attempt)
                continue
            raise CaptureError(
                f"Wayback CDX rate-limited or unavailable ({response.status_code})"
            )
        response.raise_for_status()
        rows = response.json()
        return _pick_nearest_cdx_timestamp(rows, capture_date)
    raise CaptureError(
        f"Wayback CDX rate-limited or unavailable ({last_status})"
    )


async def _fetch_snapshot_html(
    client: httpx.AsyncClient,
    seed_url: str,
    timestamp: str,
) -> tuple[str, str, int]:
    """Fetch archived HTML; return body, archive URL, and HTTP status."""
    archive_url = f"{ARCHIVE_BASE}/{timestamp}/{seed_url}"
    last_status = 0
    for attempt in range(1, _CDX_RETRIES + 1):
        response = await client.get(archive_url, follow_redirects=True)
        last_status = response.status_code
        if response.status_code in {429, 503}:
            if attempt < _CDX_RETRIES:
                await asyncio.sleep(_CDX_RETRY_SLEEP_SECONDS * attempt)
                continue
            raise CaptureError(
                f"Wayback snapshot rate-limited or unavailable ({response.status_code})"
            )
        return response.text, archive_url, response.status_code
    raise CaptureError(
        f"Wayback snapshot rate-limited or unavailable ({last_status})"
    )


def _raw_artifact_path(bank_id: str, capture_date: date, platform: Platform) -> Path:
    return (
        INTELLIGENCE_DATA_DIR
        / "raw"
        / capture_date.isoformat()
        / bank_id
        / f"wayback_{platform.value}.html"
    )


async def capture(
    bank_id: str,
    cohort_entry: CohortEntry,
    capture_date: date,
) -> CaptureResult:
    """
    Pull historical follower counts from Wayback snapshots for cohort wayback_seeds.

    Returns CaptureResult with SocialMetric rows per seed; records non-fatal
    failures in errors without substituting synthetic follower counts.
    """
    user_agent = get_user_agent()
    rate_limit = get_rate_limit_seconds()
    headers = {"User-Agent": user_agent}

    social_metrics: list[SocialMetric] = []
    raw_artifacts: dict[str, str] = {}
    errors: list[str] = []
    fetched_at = datetime.now(timezone.utc)

    seeds = cohort_entry.wayback_seeds
    attempted_platforms = _attempted_platforms_from_seeds(seeds)
    if not seeds:
        return CaptureResult(
            bank_id=bank_id,
            capture_date=capture_date,
            attempted_platforms=attempted_platforms,
            errors=["wayback: no wayback_seeds configured for this bank"],
        )

    async with httpx.AsyncClient(headers=headers, timeout=60.0) as client:
        for index, seed_url in enumerate(seeds):
            if index > 0:
                await asyncio.sleep(rate_limit)

            platform = _platform_for_url(seed_url)
            if platform is None:
                errors.append(f"wayback: unsupported seed URL {seed_url}")
                continue

            try:
                timestamp = await _fetch_cdx_timestamp(client, seed_url, capture_date)
                if not timestamp:
                    errors.append(
                        "wayback: no snapshot within "
                        f"±{CDX_WINDOW_DAYS} days of {capture_date.isoformat()} "
                        f"for {seed_url}"
                    )
                    continue

                html, archive_url, http_status = await _fetch_snapshot_html(
                    client, seed_url, timestamp
                )
                await asyncio.sleep(rate_limit)

                artifact_path = _raw_artifact_path(bank_id, capture_date, platform)
                artifact_path.parent.mkdir(parents=True, exist_ok=True)
                artifact_path.write_text(html, encoding="utf-8")
                rel_path = str(artifact_path.relative_to(REPO_ROOT))
                raw_artifacts[f"wayback_{platform.value}"] = rel_path

                followers = _parse_follower_count(html, platform)
                social_metrics.append(
                    SocialMetric(
                        bank_id=bank_id,
                        platform=platform,
                        capture_date=capture_date,
                        followers=followers,
                        source=SourceProvenance(
                            url=seed_url,
                            fetched_at=fetched_at,
                            http_status=http_status,
                            method="wayback",
                            archive_url=archive_url,
                        ),
                    )
                )
                if followers is None:
                    errors.append(
                        f"wayback: could not parse followers for {seed_url} ({platform.value})"
                    )
            except CaptureError:
                raise
            except httpx.HTTPError as exc:
                errors.append(f"wayback: HTTP error for {seed_url}: {exc}")
            except Exception as exc:
                errors.append(f"wayback: failed for {seed_url}: {exc}")

    return CaptureResult(
        bank_id=bank_id,
        capture_date=capture_date,
        social_metrics=social_metrics,
        raw_artifacts=raw_artifacts,
        errors=errors,
        attempted_platforms=attempted_platforms,
    )

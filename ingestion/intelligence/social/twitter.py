"""Twitter/X public metrics; live scrape with Wayback fallback.

Architecture notes this module is ``mostly Wayback for history`` — live X/Twitter
pages are often JS shells without follower meta. Flow:

1. Soft-skip when ``social.twitter`` is null
2. Attempt a public live fetch of ``https://x.com/{handle}``
3. If followers cannot be parsed, fall back to Wayback CDX (±7 days) for
   ``twitter.com`` / ``x.com`` profile URLs (reuses ``wayback`` helpers)

Never invents follower counts. Raises ``CaptureError`` on rate-limit / hard
failures from Wayback CDX or snapshot fetches.
"""
from __future__ import annotations

import asyncio
import re
from datetime import date, datetime, timezone
from html import unescape
from pathlib import Path
from typing import Optional

import httpx

from backend.app.services.document_ingestion import INTELLIGENCE_DATA_DIR, REPO_ROOT
from ingestion.intelligence.cohort import CohortEntry, get_rate_limit_seconds, get_user_agent
from ingestion.intelligence.errors import CaptureError
from ingestion.intelligence.social import wayback
from ingestion.intelligence.types import (
    CaptureResult,
    Platform,
    SocialMetric,
    SourceProvenance,
)

_OG_DESCRIPTION_RE = re.compile(
    r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_OG_DESCRIPTION_RE_ALT = re.compile(
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:description["\']',
    re.IGNORECASE,
)
_FOLLOWERS_COUNT_JSON_RE = re.compile(r'"followers_count"\s*:\s*(\d+)')
_FOLLOWERS_TEXT_RE = re.compile(
    r"(?P<followers>[\d,.]+[KMB]?)\s+[Ff]ollowers\b",
)
_SHELL_MARKERS = (
    "abs.twimg.com",
    "api.x.com",
)


def normalize_handle(handle: str) -> str:
    """Strip @ and URL noise; return bare Twitter/X username."""
    value = handle.strip()
    value = re.sub(
        r"^https?://(www\.)?(twitter\.com|x\.com)/",
        "",
        value,
        flags=re.IGNORECASE,
    )
    value = value.strip("/")
    value = value.split("/")[0].split("?")[0]
    value = value.lstrip("@").strip()
    if not value or not re.fullmatch(r"[A-Za-z0-9_]+", value):
        raise ValueError(f"invalid twitter handle: {handle!r}")
    return value


def profile_urls(handle: str) -> list[str]:
    """Candidate public profile URLs (x.com preferred, twitter.com for archives)."""
    user = normalize_handle(handle)
    return [
        f"https://x.com/{user}",
        f"https://twitter.com/{user}",
    ]


def parse_compact_count(raw: str) -> Optional[int]:
    """Parse ``12,345`` / ``1.2K`` / ``3M`` style counts."""
    cleaned = raw.replace(",", "").strip().upper()
    if not cleaned:
        return None
    multiplier = 1
    if cleaned.endswith("K"):
        multiplier = 1_000
        cleaned = cleaned[:-1]
    elif cleaned.endswith("M"):
        multiplier = 1_000_000
        cleaned = cleaned[:-1]
    elif cleaned.endswith("B"):
        multiplier = 1_000_000_000
        cleaned = cleaned[:-1]
    try:
        value = int(float(cleaned) * multiplier)
    except ValueError:
        return None
    return value if value >= 0 else None


def parse_profile_counts(html: str) -> tuple[Optional[int], list[str]]:
    """Return (followers, soft_errors) from live or archived Twitter/X HTML."""
    errors: list[str] = []

    json_match = _FOLLOWERS_COUNT_JSON_RE.search(html)
    if json_match:
        followers = parse_compact_count(json_match.group(1))
        if followers is not None:
            return followers, errors

    for pattern in (_OG_DESCRIPTION_RE, _OG_DESCRIPTION_RE_ALT):
        meta = pattern.search(html)
        if not meta:
            continue
        description = unescape(meta.group(1))
        text_match = _FOLLOWERS_TEXT_RE.search(description)
        if text_match:
            followers = parse_compact_count(text_match.group("followers"))
            if followers is not None:
                return followers, errors

    # Fallback: plain "N followers" (also used by Wayback HTML parsing).
    via_wayback = wayback._parse_follower_count(html, Platform.TWITTER)
    if via_wayback is not None:
        return via_wayback, errors

    plain = _FOLLOWERS_TEXT_RE.search(html)
    if plain:
        followers = parse_compact_count(plain.group("followers"))
        if followers is not None:
            return followers, errors

    errors.append("twitter: no follower count found in profile HTML")
    return None, errors


def looks_like_js_shell(html: str) -> bool:
    """True when the response is an X/Twitter app shell without profile meta."""
    if _FOLLOWERS_COUNT_JSON_RE.search(html):
        return False
    if _OG_DESCRIPTION_RE.search(html) or _OG_DESCRIPTION_RE_ALT.search(html):
        return False
    lowered = html[:6000].lower()
    return any(marker in lowered for marker in _SHELL_MARKERS) and len(html) < 50_000


def _raw_artifact_path(bank_id: str, capture_date: date, suffix: str) -> Path:
    return (
        INTELLIGENCE_DATA_DIR
        / "raw"
        / capture_date.isoformat()
        / bank_id
        / f"twitter_{suffix}.html"
    )


async def _fetch_live_html(
    client: httpx.AsyncClient,
    url: str,
) -> tuple[str, int, str]:
    response = await client.get(url, follow_redirects=True)
    if response.status_code in {429, 503}:
        raise CaptureError(
            f"Twitter/X rate-limited or unavailable ({response.status_code})"
        )
    if response.status_code in {401, 403}:
        raise CaptureError(
            f"Twitter/X auth wall or blocked response ({response.status_code})"
        )
    if response.status_code >= 400:
        raise CaptureError(f"Twitter/X HTTP {response.status_code} for {url}")
    return response.text, response.status_code, str(response.url)


async def _wayback_fallback(
    client: httpx.AsyncClient,
    handle: str,
    capture_date: date,
    bank_id: str,
) -> tuple[Optional[int], Optional[str], Optional[int], Optional[str], list[str]]:
    """Try Wayback snapshots for profile URLs.

    Returns (followers, archive_url, http_status, artifact_relpath, errors).
    """
    errors: list[str] = []
    rate_limit = get_rate_limit_seconds()

    for index, seed_url in enumerate(profile_urls(handle)):
        if index > 0:
            await asyncio.sleep(rate_limit)
        timestamp = await wayback._fetch_cdx_timestamp(client, seed_url, capture_date)
        if not timestamp:
            errors.append(
                f"twitter: no Wayback snapshot within ±{wayback.CDX_WINDOW_DAYS} "
                f"days of {capture_date.isoformat()} for {seed_url}"
            )
            continue

        await asyncio.sleep(rate_limit)
        html, archive_url, http_status = await wayback._fetch_snapshot_html(
            client, seed_url, timestamp
        )
        artifact_path = _raw_artifact_path(bank_id, capture_date, "wayback")
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(html, encoding="utf-8")
        rel_path = str(artifact_path.relative_to(REPO_ROOT))

        followers, parse_errors = parse_profile_counts(html)
        errors.extend(parse_errors)
        return followers, archive_url, http_status, rel_path, errors

    return None, None, None, None, errors


async def capture(
    bank_id: str,
    cohort_entry: CohortEntry,
    capture_date: date,
) -> CaptureResult:
    """
    Pull Twitter/X follower snapshot (live, then Wayback fallback).

    Returns CaptureResult with at most one SocialMetric. Raises CaptureError on
    rate-limit / hard HTTP failures — never substitutes synthetic counts.
    """
    raw_handle = (cohort_entry.social.twitter or "").strip()
    if not raw_handle:
        return CaptureResult(
            bank_id=bank_id,
            capture_date=capture_date,
            attempted_platforms=[],
            errors=["twitter: no handle configured for this bank"],
        )

    try:
        handle = normalize_handle(raw_handle)
    except ValueError as exc:
        return CaptureResult(
            bank_id=bank_id,
            capture_date=capture_date,
            attempted_platforms=[Platform.TWITTER],
            errors=[f"twitter: {exc}"],
        )

    attempted_platforms = [Platform.TWITTER]
    errors: list[str] = []
    social_metrics: list[SocialMetric] = []
    raw_artifacts: dict[str, str] = {}
    fetched_at = datetime.now(timezone.utc)

    headers = {
        "User-Agent": get_user_agent(),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }
    live_url = profile_urls(handle)[0]

    async with httpx.AsyncClient(headers=headers, timeout=60.0) as client:
        live_followers: Optional[int] = None
        live_status = 200
        live_final_url = live_url

        try:
            html, live_status, live_final_url = await _fetch_live_html(client, live_url)
            artifact_path = _raw_artifact_path(bank_id, capture_date, "live")
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_path.write_text(html, encoding="utf-8")
            raw_artifacts["twitter_live"] = str(artifact_path.relative_to(REPO_ROOT))

            if looks_like_js_shell(html):
                errors.append("twitter: live page is a JS shell without follower meta")
            else:
                live_followers, parse_errors = parse_profile_counts(html)
                errors.extend(parse_errors)
        except CaptureError:
            raise
        except httpx.HTTPError as exc:
            errors.append(f"twitter: live HTTP error: {exc}")

        if live_followers is not None:
            social_metrics.append(
                SocialMetric(
                    bank_id=bank_id,
                    platform=Platform.TWITTER,
                    capture_date=capture_date,
                    followers=live_followers,
                    source=SourceProvenance(
                        url=live_final_url,
                        fetched_at=fetched_at,
                        http_status=live_status,
                        method="scrape",
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

        # Wayback fallback (primary path for Issue 01 given live X shells).
        await asyncio.sleep(get_rate_limit_seconds())
        try:
            (
                wb_followers,
                archive_url,
                wb_status,
                wb_artifact,
                wb_errors,
            ) = await _wayback_fallback(client, handle, capture_date, bank_id)
        except CaptureError:
            raise
        except httpx.HTTPError as exc:
            raise CaptureError(f"twitter: Wayback HTTP error: {exc}") from exc

        errors.extend(wb_errors)
        if wb_artifact:
            raw_artifacts["twitter_wayback"] = wb_artifact

        social_metrics.append(
            SocialMetric(
                bank_id=bank_id,
                platform=Platform.TWITTER,
                capture_date=capture_date,
                followers=wb_followers,
                source=SourceProvenance(
                    url=live_url,
                    fetched_at=fetched_at,
                    http_status=wb_status if wb_status is not None else live_status,
                    method="wayback" if archive_url else "scrape",
                    archive_url=archive_url,
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

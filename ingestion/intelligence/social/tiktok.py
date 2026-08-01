"""Public TikTok profile scraping.

Fetches the public ``/@handle`` page (no login, no cookies) and parses
follower counts from ``og:description`` or embedded
``__UNIVERSAL_DATA_FOR_REHYDRATION__`` JSON. TikTok often serves a Slardar WAF
challenge to non-browser clients — that raises ``CaptureError`` (never
synthetic counts).

Cohort Issue 01 currently has ``tiktok: null`` for all six banks; those banks
soft-skip without attempting the platform.
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any, Optional

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

_OG_DESCRIPTION_RE = re.compile(
    r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_OG_DESCRIPTION_RE_ALT = re.compile(
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:description["\']',
    re.IGNORECASE,
)
# "50.2M Followers, 123 Following, 456 Likes" (order can vary slightly)
_META_FOLLOWERS_RE = re.compile(
    r"(?P<followers>[\d,.]+[KMB]?)\s+Followers",
    re.IGNORECASE,
)
_UNIVERSAL_DATA_RE = re.compile(
    r'<script[^>]+id=["\']__UNIVERSAL_DATA_FOR_REHYDRATION__["\'][^>]*>\s*(\{.*?\})\s*</script>',
    re.IGNORECASE | re.DOTALL,
)
_WAF_MARKERS = (
    "slardarwaf",
    "slardar-config",
    "tiktok_web_login_static/slardar",
)


def normalize_handle(handle: str) -> str:
    """Strip @ and URL noise; return bare TikTok username."""
    value = handle.strip()
    value = re.sub(r"^https?://(www\.)?tiktok\.com/", "", value, flags=re.IGNORECASE)
    value = value.strip("/")
    value = value.split("/")[0].split("?")[0]
    value = value.lstrip("@").strip()
    if not value or not re.fullmatch(r"[A-Za-z0-9._]+", value):
        raise ValueError(f"invalid tiktok handle: {handle!r}")
    return value


def profile_url(handle: str) -> str:
    """Canonical public profile URL for provenance."""
    return f"https://www.tiktok.com/@{normalize_handle(handle)}"


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


def _extract_og_description(html: str) -> Optional[str]:
    for pattern in (_OG_DESCRIPTION_RE, _OG_DESCRIPTION_RE_ALT):
        match = pattern.search(html)
        if match:
            return unescape(match.group(1))
    return None


def _walk_for_follower_count(node: Any) -> Optional[int]:
    """Depth-first search for followerCount / fans keys in rehydration JSON."""
    if isinstance(node, dict):
        for key in ("followerCount", "follower_count", "fans"):
            if key in node:
                parsed = parse_compact_count(str(node[key]))
                if parsed is not None:
                    return parsed
        for value in node.values():
            found = _walk_for_follower_count(value)
            if found is not None:
                return found
    elif isinstance(node, list):
        for item in node:
            found = _walk_for_follower_count(item)
            if found is not None:
                return found
    return None


def parse_profile_counts(html: str) -> tuple[Optional[int], list[str]]:
    """Return (followers, soft_errors) from public TikTok profile HTML."""
    errors: list[str] = []

    universal = _UNIVERSAL_DATA_RE.search(html)
    if universal:
        try:
            payload = json.loads(universal.group(1))
        except json.JSONDecodeError:
            errors.append("tiktok: failed to parse __UNIVERSAL_DATA_FOR_REHYDRATION__ JSON")
        else:
            followers = _walk_for_follower_count(payload)
            if followers is not None:
                return followers, errors

    og = _extract_og_description(html)
    if og:
        match = _META_FOLLOWERS_RE.search(og)
        if match:
            followers = parse_compact_count(match.group("followers"))
            if followers is not None:
                return followers, errors
            errors.append("tiktok: could not parse follower count from og:description")

    errors.append("tiktok: no follower count found in profile HTML")
    return None, errors


def looks_like_waf_challenge(html: str) -> bool:
    """True when the response is a Slardar/WAF shell rather than a profile."""
    lowered = html[:4000].lower()
    if any(marker in lowered for marker in _WAF_MARKERS):
        return True
    # Tiny challenge pages lack profile meta entirely.
    if len(html) < 5000 and "og:description" not in lowered:
        return True
    return False


def _raw_artifact_path(bank_id: str, capture_date: date) -> Path:
    return (
        INTELLIGENCE_DATA_DIR
        / "raw"
        / capture_date.isoformat()
        / bank_id
        / "tiktok_profile.html"
    )


async def _fetch_profile_html(
    client: httpx.AsyncClient,
    handle: str,
) -> tuple[str, int, str]:
    """GET the public profile page; return (html, status, final_url)."""
    url = profile_url(handle)
    response = await client.get(url, follow_redirects=True)
    html = response.text
    if response.status_code in {429, 503}:
        raise CaptureError(
            f"TikTok rate-limited or unavailable ({response.status_code}) "
            f"for @{handle}"
        )
    if response.status_code in {401, 403}:
        raise CaptureError(
            f"TikTok auth wall or blocked response ({response.status_code}) "
            f"for @{handle}"
        )
    if looks_like_waf_challenge(html):
        raise CaptureError(
            f"TikTok WAF challenge blocked public scrape for @{handle}"
        )
    if response.status_code >= 400:
        raise CaptureError(f"TikTok HTTP {response.status_code} for @{handle}")
    return html, response.status_code, str(response.url)


async def capture(
    bank_id: str,
    cohort_entry: CohortEntry,
    capture_date: date,
) -> CaptureResult:
    """
    Pull public follower snapshot for the bank's TikTok profile.

    Returns CaptureResult with at most one SocialMetric. Raises CaptureError on
    WAF / rate-limit / auth walls — never substitutes synthetic follower counts.
    """
    raw_handle = (cohort_entry.social.tiktok or "").strip()
    if not raw_handle:
        return CaptureResult(
            bank_id=bank_id,
            capture_date=capture_date,
            attempted_platforms=[],
            errors=["tiktok: no handle configured for this bank"],
        )

    try:
        handle = normalize_handle(raw_handle)
    except ValueError as exc:
        return CaptureResult(
            bank_id=bank_id,
            capture_date=capture_date,
            attempted_platforms=[Platform.TIKTOK],
            errors=[f"tiktok: {exc}"],
        )

    attempted_platforms = [Platform.TIKTOK]
    errors: list[str] = []
    social_metrics: list[SocialMetric] = []
    raw_artifacts: dict[str, str] = {}
    fetched_at = datetime.now(timezone.utc)

    headers = {
        "User-Agent": get_user_agent(),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }
    async with httpx.AsyncClient(headers=headers, timeout=60.0) as client:
        try:
            html, http_status, final_url = await _fetch_profile_html(client, handle)
        except CaptureError:
            raise
        except httpx.HTTPError as exc:
            raise CaptureError(f"TikTok HTTP error for @{handle}: {exc}") from exc

    artifact_path = _raw_artifact_path(bank_id, capture_date)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(html, encoding="utf-8")
    raw_artifacts["tiktok_profile"] = str(artifact_path.relative_to(REPO_ROOT))

    followers, parse_errors = parse_profile_counts(html)
    errors.extend(parse_errors)

    social_metrics.append(
        SocialMetric(
            bank_id=bank_id,
            platform=Platform.TIKTOK,
            capture_date=capture_date,
            followers=followers,
            source=SourceProvenance(
                url=final_url if final_url.startswith("http") else profile_url(handle),
                fetched_at=fetched_at,
                http_status=http_status,
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

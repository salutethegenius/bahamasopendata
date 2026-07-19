"""Public Facebook page scraping.

Fetches the public page HTML (no login, no cookies) and parses follower /
like counts from ``og:description`` and embedded public strings. Raises
``CaptureError`` on rate-limit / auth walls; never invents counts.

Playwright remains available for a future fallback if meta tags disappear;
httpx + public HTML is sufficient for cohort business pages today.
"""
from __future__ import annotations

import html as html_lib
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

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
# og:description: "Name, City. 6,649 likes · 27 talking about this · …"
_OG_LIKES_RE = re.compile(
    r"(?P<likes>[\d,.]+[KMB]?)\s+likes\b",
    re.IGNORECASE,
)
# Embedded public string: "text":"6.6K followers"
_EMBEDDED_FOLLOWERS_RE = re.compile(
    r'"text"\s*:\s*"(?P<followers>[\d,.]+[KMB]?)\s+followers"',
    re.IGNORECASE,
)
_PLAIN_FOLLOWERS_RE = re.compile(
    r"(?P<followers>[\d,.]+[KMB]?)\s+followers\b",
    re.IGNORECASE,
)


def normalize_handle(handle: str) -> str:
    """Strip URL noise; return bare Facebook page slug / id."""
    value = handle.strip()
    value = re.sub(r"^https?://(www\.)?facebook\.com/", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^https?://(www\.)?fb\.com/", "", value, flags=re.IGNORECASE)
    value = value.strip("/")
    value = value.split("/")[0].split("?")[0]
    value = value.lstrip("@").strip()
    if not value or not re.fullmatch(r"[A-Za-z0-9.]+", value):
        raise ValueError(f"invalid facebook handle: {handle!r}")
    return value


def page_url(handle: str) -> str:
    """Canonical public page URL for provenance."""
    return f"https://www.facebook.com/{normalize_handle(handle)}/"


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
            return html_lib.unescape(match.group(1))
    return None


def _is_exact_count_token(raw: str) -> bool:
    """True when the token has no K/M/B compaction suffix."""
    return not raw.strip().upper().endswith(("K", "M", "B"))


def parse_page_counts(html: str) -> tuple[Optional[int], list[str]]:
    """Return (followers, soft_errors) from public Facebook page HTML.

    Preference order (most precise first):
      1. Exact (non-compact) follower count from embedded/plain text
      2. Exact ``N likes`` from og:description (noted as likes proxy)
      3. Compact follower count (e.g. ``6.6K``)
    """
    errors: list[str] = []
    compact_followers: Optional[int] = None

    for match in list(_EMBEDDED_FOLLOWERS_RE.finditer(html)) + list(
        _PLAIN_FOLLOWERS_RE.finditer(html)
    ):
        token = match.group("followers")
        parsed = parse_compact_count(token)
        if parsed is None:
            continue
        if _is_exact_count_token(token):
            return parsed, errors
        if compact_followers is None:
            compact_followers = parsed

    og = _extract_og_description(html)
    if og:
        likes_match = _OG_LIKES_RE.search(og)
        if likes_match:
            likes_token = likes_match.group("likes")
            likes = parse_compact_count(likes_token)
            if likes is not None and _is_exact_count_token(likes_token):
                errors.append(
                    "facebook: using exact page likes "
                    f"({likes}) as followers proxy"
                )
                return likes, errors

    if compact_followers is not None:
        return compact_followers, errors

    if og:
        likes_match = _OG_LIKES_RE.search(og)
        if likes_match:
            likes = parse_compact_count(likes_match.group("likes"))
            if likes is not None:
                errors.append(
                    "facebook: follower count unavailable; using page likes "
                    f"({likes}) as followers proxy"
                )
                return likes, errors

    errors.append("facebook: no follower or likes count found in page HTML")
    return None, errors


def _looks_like_auth_wall(status_code: int, html: str) -> bool:
    if status_code in {401, 403}:
        return True
    lowered = html[:12000].lower()
    has_counts = (
        _EMBEDDED_FOLLOWERS_RE.search(html) is not None
        or _OG_LIKES_RE.search(html) is not None
    )
    if ("login" in lowered or "log in" in lowered) and not has_counts:
        if "og:description" not in lowered:
            return True
    return False


def _raw_artifact_path(bank_id: str, capture_date: date) -> Path:
    return (
        INTELLIGENCE_DATA_DIR
        / "raw"
        / capture_date.isoformat()
        / bank_id
        / "facebook_profile.html"
    )


async def _fetch_page_html(
    client: httpx.AsyncClient,
    handle: str,
) -> tuple[str, int, str]:
    """GET the public page; return (html, status, final_url)."""
    url = page_url(handle)
    response = await client.get(url, follow_redirects=True)
    html = response.text
    if response.status_code in {429, 503}:
        raise CaptureError(
            f"Facebook rate-limited or unavailable ({response.status_code}) "
            f"for {handle}"
        )
    if _looks_like_auth_wall(response.status_code, html):
        raise CaptureError(
            f"Facebook auth wall or blocked response ({response.status_code}) "
            f"for {handle}"
        )
    if response.status_code >= 400:
        raise CaptureError(f"Facebook HTTP {response.status_code} for {handle}")
    return html, response.status_code, str(response.url)


async def capture(
    bank_id: str,
    cohort_entry: CohortEntry,
    capture_date: date,
) -> CaptureResult:
    """
    Pull public follower/likes snapshot for the bank's Facebook page.

    Returns CaptureResult with at most one SocialMetric. Raises CaptureError on
    rate-limit / auth walls — never substitutes synthetic follower counts.
    """
    raw_handle = (cohort_entry.social.facebook or "").strip()
    if not raw_handle:
        return CaptureResult(
            bank_id=bank_id,
            capture_date=capture_date,
            attempted_platforms=[],
            errors=["facebook: no handle configured for this bank"],
        )

    try:
        handle = normalize_handle(raw_handle)
    except ValueError as exc:
        return CaptureResult(
            bank_id=bank_id,
            capture_date=capture_date,
            attempted_platforms=[Platform.FACEBOOK],
            errors=[f"facebook: {exc}"],
        )

    attempted_platforms = [Platform.FACEBOOK]
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
            html, http_status, final_url = await _fetch_page_html(client, handle)
        except CaptureError:
            raise
        except httpx.HTTPError as exc:
            raise CaptureError(f"Facebook HTTP error for {handle}: {exc}") from exc

    artifact_path = _raw_artifact_path(bank_id, capture_date)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(html, encoding="utf-8")
    raw_artifacts["facebook_profile"] = str(artifact_path.relative_to(REPO_ROOT))

    followers, parse_errors = parse_page_counts(html)
    errors.extend(parse_errors)

    social_metrics.append(
        SocialMetric(
            bank_id=bank_id,
            platform=Platform.FACEBOOK,
            capture_date=capture_date,
            followers=followers,
            source=SourceProvenance(
                url=final_url if final_url.startswith("http") else page_url(handle),
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

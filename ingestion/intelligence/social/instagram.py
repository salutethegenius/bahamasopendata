"""Public Instagram business profile scraping.

Fetches the public profile HTML (no login, no cookies) and parses follower /
post counts from ``og:description`` / ``meta description`` — the same public
strings Instagram exposes to search engines. Raises ``CaptureError`` on
rate-limit / auth walls; never invents follower counts.

Playwright is reserved as a future fallback if meta tags disappear; the
current public HTML response is sufficient for cohort business profiles.
"""
from __future__ import annotations

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

# "2,289 Followers, 32 Following, 861 Posts" or "1.2M Followers, …"
_META_COUNTS_RE = re.compile(
    r"(?P<followers>[\d,.]+[KMB]?)\s+Followers,\s+"
    r"(?P<following>[\d,.]+[KMB]?)\s+Following,\s+"
    r"(?P<posts>[\d,.]+[KMB]?)\s+Posts",
    re.IGNORECASE,
)
_OG_DESCRIPTION_RE = re.compile(
    r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_OG_DESCRIPTION_RE_ALT = re.compile(
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:description["\']',
    re.IGNORECASE,
)
_META_DESCRIPTION_RE = re.compile(
    r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_META_DESCRIPTION_RE_ALT = re.compile(
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']description["\']',
    re.IGNORECASE,
)
_LOGIN_MARKERS = (
    "accounts/login",
    "logininstagrampage",
    '"loginForm"',
)


def normalize_handle(handle: str) -> str:
    """Strip @ and URL noise; return bare Instagram username."""
    value = handle.strip()
    value = re.sub(r"^https?://(www\.)?instagram\.com/", "", value, flags=re.IGNORECASE)
    value = value.strip("/")
    value = value.split("/")[0].split("?")[0]
    value = value.lstrip("@").strip()
    if not value or not re.fullmatch(r"[A-Za-z0-9._]+", value):
        raise ValueError(f"invalid instagram handle: {handle!r}")
    return value


def profile_url(handle: str) -> str:
    """Canonical public profile URL for provenance."""
    return f"https://www.instagram.com/{normalize_handle(handle)}/"


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


def _html_unescape_basic(text: str) -> str:
    return (
        text.replace("&#064;", "@")
        .replace("&amp;", "&")
        .replace("&quot;", '"')
        .replace("&#x2022;", "•")
    )


def extract_description_candidates(html: str) -> list[str]:
    """Collect og:description / meta description content strings from HTML."""
    candidates: list[str] = []
    for pattern in (
        _OG_DESCRIPTION_RE,
        _OG_DESCRIPTION_RE_ALT,
        _META_DESCRIPTION_RE,
        _META_DESCRIPTION_RE_ALT,
    ):
        for match in pattern.finditer(html):
            candidates.append(_html_unescape_basic(match.group(1)))
    return candidates


def parse_profile_counts(html: str) -> tuple[Optional[int], Optional[int], list[str]]:
    """Return (followers, posts_total_hint, soft_errors) from public meta tags.

    ``posts`` from the meta string is lifetime post count, not posts-in-window,
    so callers should not map it onto ``SocialMetric.posts_in_window``.
    """
    errors: list[str] = []
    for description in extract_description_candidates(html):
        match = _META_COUNTS_RE.search(description)
        if not match:
            continue
        followers = parse_compact_count(match.group("followers"))
        posts = parse_compact_count(match.group("posts"))
        if followers is None:
            errors.append("instagram: could not parse follower count from meta description")
        return followers, posts, errors

    errors.append("instagram: no follower meta description found in profile HTML")
    return None, None, errors


def _looks_like_auth_wall(status_code: int, html: str) -> bool:
    if status_code in {401, 403}:
        return True
    lowered = html[:8000].lower()
    has_login = any(marker in lowered for marker in _LOGIN_MARKERS)
    has_counts = _META_COUNTS_RE.search(html) is not None
    # Login chrome alone is common on public pages; only treat as wall when
    # follower meta is missing AND login markers dominate.
    if has_login and not has_counts and "og:description" not in lowered:
        return True
    return False


def _raw_artifact_path(bank_id: str, capture_date: date) -> Path:
    return (
        INTELLIGENCE_DATA_DIR
        / "raw"
        / capture_date.isoformat()
        / bank_id
        / "instagram_profile.html"
    )


async def _fetch_profile_html(
    client: httpx.AsyncClient,
    handle: str,
) -> tuple[str, int, str]:
    """GET the public profile page; return (html, status, url)."""
    url = profile_url(handle)
    # Avoid path-injection surprises; username already validated.
    response = await client.get(url, follow_redirects=True)
    html = response.text
    if response.status_code in {429, 503}:
        raise CaptureError(
            f"Instagram rate-limited or unavailable ({response.status_code}) "
            f"for @{handle}"
        )
    if _looks_like_auth_wall(response.status_code, html):
        raise CaptureError(
            f"Instagram auth wall or blocked response ({response.status_code}) "
            f"for @{handle}"
        )
    if response.status_code >= 400:
        raise CaptureError(
            f"Instagram HTTP {response.status_code} for @{handle}"
        )
    return html, response.status_code, str(response.url)


async def capture(
    bank_id: str,
    cohort_entry: CohortEntry,
    capture_date: date,
) -> CaptureResult:
    """
    Pull public follower snapshot for the bank's Instagram business profile.

    Returns CaptureResult with at most one SocialMetric. Raises CaptureError on
    rate-limit / auth walls — never substitutes synthetic follower counts.
    """
    raw_handle = (cohort_entry.social.instagram or "").strip()
    if not raw_handle:
        return CaptureResult(
            bank_id=bank_id,
            capture_date=capture_date,
            attempted_platforms=[],
            errors=["instagram: no handle configured for this bank"],
        )

    try:
        handle = normalize_handle(raw_handle)
    except ValueError as exc:
        return CaptureResult(
            bank_id=bank_id,
            capture_date=capture_date,
            attempted_platforms=[Platform.INSTAGRAM],
            errors=[f"instagram: {exc}"],
        )

    attempted_platforms = [Platform.INSTAGRAM]
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
            raise CaptureError(f"Instagram HTTP error for @{handle}: {exc}") from exc

    artifact_path = _raw_artifact_path(bank_id, capture_date)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(html, encoding="utf-8")
    raw_artifacts["instagram_profile"] = str(artifact_path.relative_to(REPO_ROOT))

    followers, _posts_total, parse_errors = parse_profile_counts(html)
    errors.extend(parse_errors)
    if _posts_total is not None:
        # Lifetime post count is useful context but is not posts_in_window.
        errors.append(
            f"instagram: profile shows {_posts_total} lifetime posts "
            "(not mapped to posts_in_window)"
        )

    social_metrics.append(
        SocialMetric(
            bank_id=bank_id,
            platform=Platform.INSTAGRAM,
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

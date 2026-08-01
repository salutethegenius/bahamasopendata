"""Cross-reference TikTok and YouTube stats via Social Blade.

Fetches public Social Blade profile pages (no login) and parses subscriber /
follower counts from embedded ``__NEXT_DATA__`` JSON. Used as a cross-check
for YouTube (and TikTok when cohort handles exist). Raises ``CaptureError`` on
rate-limit / auth walls — never invents counts.
"""
from __future__ import annotations

import asyncio
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional

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

_NEXT_DATA_RE = re.compile(
    r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>\s*(\{.*?\})\s*</script>',
    re.IGNORECASE | re.DOTALL,
)
_CHANNEL_ID_RE = re.compile(r"^UC[\w-]{22}$")


def normalize_youtube_target(handle: str) -> tuple[str, str]:
    """Return (kind, value) where kind is ``channel`` or ``handle``."""
    value = handle.strip()
    value = re.sub(
        r"^https?://(www\.)?youtube\.com/",
        "",
        value,
        flags=re.IGNORECASE,
    )
    value = value.strip("/")
    if value.startswith("channel/"):
        value = value.split("/", 1)[1]
    if value.startswith("@"):
        value = value[1:]
    value = value.split("/")[0].split("?")[0].strip()
    if not value:
        raise ValueError(f"invalid youtube handle: {handle!r}")
    if _CHANNEL_ID_RE.match(value):
        return "channel", value
    return "handle", value.lstrip("@")


def normalize_tiktok_handle(handle: str) -> str:
    """Return bare TikTok username."""
    value = handle.strip()
    value = re.sub(r"^https?://(www\.)?tiktok\.com/", "", value, flags=re.IGNORECASE)
    value = value.strip("/").split("/")[0].split("?")[0]
    value = value.lstrip("@").strip()
    if not value or not re.fullmatch(r"[A-Za-z0-9._]+", value):
        raise ValueError(f"invalid tiktok handle: {handle!r}")
    return value


def socialblade_youtube_url(handle: str) -> str:
    kind, value = normalize_youtube_target(handle)
    if kind == "channel":
        return f"https://socialblade.com/youtube/channel/{value}"
    return f"https://socialblade.com/youtube/handle/{value}"


def socialblade_tiktok_url(handle: str) -> str:
    return f"https://socialblade.com/tiktok/user/{normalize_tiktok_handle(handle)}"


def _parse_int(raw: Any) -> Optional[int]:
    if raw is None or isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        value = int(raw)
        return value if value >= 0 else None
    if isinstance(raw, str):
        cleaned = raw.replace(",", "").strip()
        if not cleaned:
            return None
        try:
            value = int(float(cleaned))
        except ValueError:
            return None
        return value if value >= 0 else None
    return None


def extract_next_data(html: str) -> Optional[dict[str, Any]]:
    """Parse the ``__NEXT_DATA__`` JSON blob from a Social Blade page."""
    match = _NEXT_DATA_RE.search(html)
    if not match:
        return None
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _primary_entity_data(next_data: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Return the main channel/user ``state.data`` object from trpcState."""
    try:
        queries = (
            next_data.get("props", {})
            .get("pageProps", {})
            .get("trpcState", {})
            .get("json", {})
            .get("queries", [])
        )
    except AttributeError:
        return None
    if not isinstance(queries, list):
        return None
    for query in queries:
        if not isinstance(query, dict):
            continue
        data = (query.get("state") or {}).get("data")
        if isinstance(data, dict) and (
            "subscribers" in data or "followers" in data or "stats" in data
        ):
            return data
    return None


def parse_youtube_counts(html: str) -> tuple[Optional[int], Optional[int], list[str]]:
    """Return (subscribers, views, soft_errors) from a YouTube Social Blade page."""
    errors: list[str] = []
    next_data = extract_next_data(html)
    if next_data is None:
        errors.append("socialblade: no __NEXT_DATA__ on YouTube page")
        return None, None, errors

    entity = _primary_entity_data(next_data)
    if entity is None:
        errors.append("socialblade: no YouTube entity data in __NEXT_DATA__")
        return None, None, errors

    stats = entity.get("stats") if isinstance(entity.get("stats"), dict) else {}
    subscribers = _parse_int(entity.get("subscribers"))
    if subscribers is None:
        subscribers = _parse_int(stats.get("subscribers"))
    views = _parse_int(entity.get("views"))
    if views is None:
        views = _parse_int(stats.get("views"))

    if subscribers is None:
        errors.append("socialblade: subscribers missing from YouTube entity data")
    return subscribers, views, errors


def parse_tiktok_counts(html: str) -> tuple[Optional[int], list[str]]:
    """Return (followers, soft_errors) from a TikTok Social Blade page."""
    errors: list[str] = []
    next_data = extract_next_data(html)
    if next_data is None:
        errors.append("socialblade: no __NEXT_DATA__ on TikTok page")
        return None, errors

    entity = _primary_entity_data(next_data)
    if entity is None:
        errors.append("socialblade: no TikTok entity data in __NEXT_DATA__")
        return None, errors

    stats = entity.get("stats") if isinstance(entity.get("stats"), dict) else {}
    followers = _parse_int(entity.get("followers"))
    if followers is None:
        followers = _parse_int(stats.get("followers"))
    if followers is None:
        errors.append("socialblade: followers missing from TikTok entity data")
    return followers, errors


def _raw_artifact_path(bank_id: str, capture_date: date, platform: Platform) -> Path:
    return (
        INTELLIGENCE_DATA_DIR
        / "raw"
        / capture_date.isoformat()
        / bank_id
        / f"socialblade_{platform.value}.html"
    )


async def _fetch_html(
    client: httpx.AsyncClient,
    url: str,
) -> tuple[str, int, str]:
    response = await client.get(url, follow_redirects=True)
    if response.status_code in {429, 503}:
        raise CaptureError(
            f"Social Blade rate-limited or unavailable ({response.status_code})"
        )
    if response.status_code in {401, 403}:
        raise CaptureError(
            f"Social Blade auth wall or blocked response ({response.status_code})"
        )
    if response.status_code == 404:
        return response.text, response.status_code, str(response.url)
    if response.status_code >= 400:
        raise CaptureError(f"Social Blade HTTP {response.status_code} for {url}")
    return response.text, response.status_code, str(response.url)


async def capture(
    bank_id: str,
    cohort_entry: CohortEntry,
    capture_date: date,
) -> CaptureResult:
    """
    Pull Social Blade cross-reference metrics for YouTube and/or TikTok.

    Returns CaptureResult with zero or more SocialMetric rows. Raises
    CaptureError on rate-limit / hard HTTP failures — never invents counts.
    """
    youtube_handle = (cohort_entry.social.youtube or "").strip()
    tiktok_handle = (cohort_entry.social.tiktok or "").strip()

    if not youtube_handle and not tiktok_handle:
        return CaptureResult(
            bank_id=bank_id,
            capture_date=capture_date,
            attempted_platforms=[],
            errors=["socialblade: no youtube or tiktok handle configured"],
        )

    attempted_platforms: list[Platform] = []
    errors: list[str] = []
    social_metrics: list[SocialMetric] = []
    raw_artifacts: dict[str, str] = {}
    fetched_at = datetime.now(timezone.utc)
    rate_limit = get_rate_limit_seconds()
    request_index = 0

    headers = {
        "User-Agent": get_user_agent(),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }

    async with httpx.AsyncClient(headers=headers, timeout=60.0) as client:
        if youtube_handle:
            attempted_platforms.append(Platform.YOUTUBE)
            try:
                url = socialblade_youtube_url(youtube_handle)
            except ValueError as exc:
                errors.append(f"socialblade: {exc}")
            else:
                if request_index > 0:
                    await asyncio.sleep(rate_limit)
                request_index += 1
                try:
                    html, http_status, final_url = await _fetch_html(client, url)
                except CaptureError:
                    raise
                except httpx.HTTPError as exc:
                    raise CaptureError(f"Social Blade HTTP error: {exc}") from exc

                artifact_path = _raw_artifact_path(
                    bank_id, capture_date, Platform.YOUTUBE
                )
                artifact_path.parent.mkdir(parents=True, exist_ok=True)
                artifact_path.write_text(html, encoding="utf-8")
                raw_artifacts["socialblade_youtube"] = str(
                    artifact_path.relative_to(REPO_ROOT)
                )

                if http_status == 404:
                    errors.append(f"socialblade: YouTube page not found ({url})")
                else:
                    subscribers, views, parse_errors = parse_youtube_counts(html)
                    errors.extend(parse_errors)
                    social_metrics.append(
                        SocialMetric(
                            bank_id=bank_id,
                            platform=Platform.YOUTUBE,
                            capture_date=capture_date,
                            followers=subscribers,
                            views=views,
                            source=SourceProvenance(
                                url=final_url,
                                fetched_at=fetched_at,
                                http_status=http_status,
                                method="socialblade",
                            ),
                        )
                    )

        if tiktok_handle:
            attempted_platforms.append(Platform.TIKTOK)
            try:
                url = socialblade_tiktok_url(tiktok_handle)
            except ValueError as exc:
                errors.append(f"socialblade: {exc}")
            else:
                if request_index > 0:
                    await asyncio.sleep(rate_limit)
                request_index += 1
                try:
                    html, http_status, final_url = await _fetch_html(client, url)
                except CaptureError:
                    raise
                except httpx.HTTPError as exc:
                    raise CaptureError(f"Social Blade HTTP error: {exc}") from exc

                artifact_path = _raw_artifact_path(
                    bank_id, capture_date, Platform.TIKTOK
                )
                artifact_path.parent.mkdir(parents=True, exist_ok=True)
                artifact_path.write_text(html, encoding="utf-8")
                raw_artifacts["socialblade_tiktok"] = str(
                    artifact_path.relative_to(REPO_ROOT)
                )

                if http_status == 404:
                    errors.append(f"socialblade: TikTok page not found ({url})")
                else:
                    followers, parse_errors = parse_tiktok_counts(html)
                    errors.extend(parse_errors)
                    social_metrics.append(
                        SocialMetric(
                            bank_id=bank_id,
                            platform=Platform.TIKTOK,
                            capture_date=capture_date,
                            followers=followers,
                            source=SourceProvenance(
                                url=final_url,
                                fetched_at=fetched_at,
                                http_status=http_status,
                                method="socialblade",
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

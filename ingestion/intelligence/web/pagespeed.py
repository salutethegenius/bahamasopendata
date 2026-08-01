"""Google PageSpeed Insights API (free tier).

Runs Lighthouse categories for the bank homepage via the public PageSpeed
Insights API. Requires ``PAGESPEED_API_KEY`` (falls back to ``YOUTUBE_API_KEY``
when both APIs share a Google Cloud key).

Maps into ``WebMetric``:
- ``authority_score`` ← performance score × 100 (0–100), with a soft-error note
  that this is Lighthouse performance — not SEO Domain Rating
- ``top_keywords`` ← ``category:score`` strings for measured categories
- ``ranking_keywords`` ← count of categories measured
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional

import httpx

from backend.app.services.document_ingestion import INTELLIGENCE_DATA_DIR, REPO_ROOT
from ingestion.intelligence.cohort import CohortEntry, get_user_agent
from ingestion.intelligence.errors import CaptureError
from ingestion.intelligence.types import (
    CaptureResult,
    Platform,
    SourceProvenance,
    WebMetric,
)
from ingestion.intelligence.web.similarweb import homepage_url

PAGESPEED_API = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
DEFAULT_STRATEGY = "mobile"
CATEGORY_ORDER = ("performance", "accessibility", "best-practices", "seo")


def _get_api_key() -> str:
    """Return PageSpeed API key from settings/env, with YouTube key fallback."""
    try:
        from backend.app.core.config import settings

        for attr in ("PAGESPEED_API_KEY", "YOUTUBE_API_KEY"):
            key = (getattr(settings, attr, None) or "").strip()
            if key:
                return key
    except Exception:
        pass
    for env_name in ("PAGESPEED_API_KEY", "YOUTUBE_API_KEY"):
        key = os.getenv(env_name, "").strip()
        if key:
            return key
    return ""


def parse_lighthouse_categories(
    payload: dict[str, Any],
) -> tuple[Optional[int], list[str], list[str]]:
    """Return (performance_0_100, category_labels, soft_errors)."""
    errors: list[str] = []
    categories = (payload.get("lighthouseResult") or {}).get("categories") or {}
    if not isinstance(categories, dict) or not categories:
        errors.append("pagespeed: no lighthouse categories in API response")
        return None, [], errors

    labels: list[str] = []
    performance: Optional[int] = None
    for name in CATEGORY_ORDER:
        entry = categories.get(name)
        if not isinstance(entry, dict):
            continue
        score = entry.get("score")
        if score is None:
            continue
        try:
            pct = int(round(float(score) * 100))
        except (TypeError, ValueError):
            continue
        if pct < 0 or pct > 100:
            continue
        labels.append(f"{name}:{pct}")
        if name == "performance":
            performance = pct

    if performance is None:
        errors.append("pagespeed: performance category score missing")
    else:
        errors.append(
            "pagespeed: authority_score holds Lighthouse performance score "
            "(0-100), not SEO Domain Rating"
        )
    if not labels:
        errors.append("pagespeed: no category scores parsed")
    return performance, labels, errors


def _raw_artifact_path(bank_id: str, capture_date: date) -> Path:
    return (
        INTELLIGENCE_DATA_DIR
        / "raw"
        / capture_date.isoformat()
        / bank_id
        / "pagespeed.json"
    )


async def _fetch_pagespeed(
    client: httpx.AsyncClient,
    api_key: str,
    page_url: str,
) -> tuple[dict[str, Any], int]:
    params = {
        "url": page_url,
        "strategy": DEFAULT_STRATEGY,
        "key": api_key,
    }
    # Request all core categories.
    # httpx encodes repeated keys; PageSpeed accepts multiple category params.
    query = [(k, v) for k, v in params.items()]
    for category in CATEGORY_ORDER:
        query.append(("category", category))

    response = await client.get(PAGESPEED_API, params=query)
    if response.status_code in {401, 403}:
        raise CaptureError(
            f"PageSpeed unauthorized or forbidden ({response.status_code})"
        )
    if response.status_code in {429, 503}:
        raise CaptureError(
            f"PageSpeed rate-limited or unavailable ({response.status_code})"
        )
    if response.status_code >= 400:
        raise CaptureError(
            f"PageSpeed HTTP {response.status_code}: {response.text[:200]}"
        )
    try:
        payload = response.json()
    except ValueError as exc:
        raise CaptureError(f"PageSpeed returned non-JSON body: {exc}") from exc
    if not isinstance(payload, dict):
        raise CaptureError("PageSpeed JSON root must be an object")
    return payload, response.status_code


async def capture(
    bank_id: str,
    cohort_entry: CohortEntry,
    capture_date: date,
) -> CaptureResult:
    """
    Pull PageSpeed Insights scores for the bank homepage.

    Returns CaptureResult with at most one WebMetric. Raises CaptureError on
    auth / rate-limit / hard API failures — never invents Lighthouse scores.
    """
    raw_domain = (cohort_entry.domain or "").strip()
    if not raw_domain:
        return CaptureResult(
            bank_id=bank_id,
            capture_date=capture_date,
            attempted_platforms=[],
            errors=["pagespeed: no domain configured for this bank"],
        )

    try:
        page_url = homepage_url(raw_domain)
    except ValueError as exc:
        return CaptureResult(
            bank_id=bank_id,
            capture_date=capture_date,
            attempted_platforms=[Platform.WEBSITE],
            errors=[f"pagespeed: {exc}"],
        )

    api_key = _get_api_key()
    if not api_key:
        raise CaptureError("PAGESPEED_API_KEY (or YOUTUBE_API_KEY fallback) is not set")

    attempted_platforms = [Platform.WEBSITE]
    errors: list[str] = []
    fetched_at = datetime.now(timezone.utc)

    headers = {"User-Agent": get_user_agent(), "Accept": "application/json"}
    async with httpx.AsyncClient(headers=headers, timeout=120.0) as client:
        try:
            payload, http_status = await _fetch_pagespeed(client, api_key, page_url)
        except CaptureError:
            raise
        except httpx.HTTPError as exc:
            raise CaptureError(f"PageSpeed HTTP error: {exc}") from exc

    artifact_path = _raw_artifact_path(bank_id, capture_date)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    performance, labels, parse_errors = parse_lighthouse_categories(payload)
    errors.extend(parse_errors)

    web_metrics = [
        WebMetric(
            bank_id=bank_id,
            capture_date=capture_date,
            authority_score=performance,
            ranking_keywords=len(labels) if labels else None,
            top_keywords=labels,
            source=SourceProvenance(
                url=page_url,
                fetched_at=fetched_at,
                http_status=http_status,
                method="api",
            ),
        )
    ]

    return CaptureResult(
        bank_id=bank_id,
        capture_date=capture_date,
        web_metrics=web_metrics,
        raw_artifacts={
            "pagespeed": str(artifact_path.relative_to(REPO_ROOT)),
        },
        errors=errors,
        attempted_platforms=attempted_platforms,
    )

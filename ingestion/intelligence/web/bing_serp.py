"""Bing Web Search API — non-branded query visibility.

.. note::
   **Not registered in Issue 01.** Bing Web Search API is discontinued for
   this imprint; module retained for tests / possible future replacement.

Runs a fixed set of Bahamian banking queries that contain **no bank brand
names**, then measures whether the bank's ``cohort.domain`` appears in the
organic web results. Emits one ``WebMetric`` with:

- ``ranking_keywords`` — count of non-branded queries where the domain ranked
- ``non_branded_search_share`` — ranking_keywords / query set size
- ``top_keywords`` — the queries where the domain appeared

Requires ``BING_SEARCH_API_KEY`` (Azure Bing Web Search v7). Raises
``CaptureError`` on auth / rate-limit failures — never invents rankings.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

import httpx

from backend.app.services.document_ingestion import INTELLIGENCE_DATA_DIR, REPO_ROOT
from ingestion.intelligence.cohort import CohortEntry, get_rate_limit_seconds, get_user_agent
from ingestion.intelligence.errors import CaptureError
from ingestion.intelligence.types import (
    CaptureResult,
    Platform,
    SourceProvenance,
    WebMetric,
)

BING_SEARCH_API = "https://api.bing.microsoft.com/v7.0/search"
RESULT_COUNT = 10

# Non-branded Bahamian banking queries — no institution names.
NON_BRANDED_QUERIES: tuple[str, ...] = (
    "bank account bahamas",
    "mortgage rates bahamas",
    "online banking bahamas",
    "personal loan bahamas",
    "credit card bahamas",
    "savings account nassau",
    "best bank in the bahamas",
    "bahamas mobile banking",
    "wire transfer bahamas",
    "checking account bahamas",
)


def _get_api_key() -> str:
    """Return the Bing Web Search API key from settings or the environment."""
    try:
        from backend.app.core.config import settings

        key = (getattr(settings, "BING_SEARCH_API_KEY", None) or "").strip()
        if key:
            return key
    except Exception:
        pass
    return os.getenv("BING_SEARCH_API_KEY", "").strip()


def normalize_domain(domain: str) -> str:
    """Strip scheme, path, and leading www."""
    value = domain.strip().lower()
    value = re.sub(r"^https?://", "", value)
    value = value.split("/")[0]
    if value.startswith("www."):
        value = value[4:]
    if not value or "." not in value:
        raise ValueError(f"invalid domain: {domain!r}")
    return value


def host_matches_domain(url: str, domain: str) -> bool:
    """True when the result URL host is the domain or a subdomain of it."""
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return False
    if host.startswith("www."):
        host = host[4:]
    return host == domain or host.endswith("." + domain)


def extract_organic_urls(payload: dict[str, Any]) -> list[str]:
    """Return organic web result URLs from a Bing Search JSON body."""
    web_pages = (payload.get("webPages") or {}).get("value") or []
    urls: list[str] = []
    for item in web_pages:
        if not isinstance(item, dict):
            continue
        url = item.get("url")
        if isinstance(url, str) and url.startswith("http"):
            urls.append(url)
    return urls


def score_query_hits(
    query_results: dict[str, list[str]],
    domain: str,
) -> tuple[int, float, list[str]]:
    """Compute (ranking_keywords, non_branded_share, top_keywords)."""
    hits: list[str] = []
    for query, urls in query_results.items():
        if any(host_matches_domain(url, domain) for url in urls):
            hits.append(query)
    total = len(query_results)
    ranking = len(hits)
    share = (ranking / total) if total else None
    return ranking, share if share is not None else 0.0, hits


def _raw_artifact_path(bank_id: str, capture_date: date) -> Path:
    return (
        INTELLIGENCE_DATA_DIR
        / "raw"
        / capture_date.isoformat()
        / bank_id
        / "bing_serp.json"
    )


async def _fetch_query(
    client: httpx.AsyncClient,
    api_key: str,
    query: str,
) -> tuple[dict[str, Any], int]:
    """Call Bing Web Search for one query; return (json, http_status)."""
    headers = {
        "Ocp-Apim-Subscription-Key": api_key,
        "User-Agent": get_user_agent(),
    }
    params = {
        "q": query,
        "count": RESULT_COUNT,
        "mkt": "en-BS",
        "safeSearch": "Moderate",
    }
    response = await client.get(BING_SEARCH_API, params=params, headers=headers)
    if response.status_code in {401, 403}:
        raise CaptureError(
            f"Bing Search unauthorized or forbidden ({response.status_code})"
        )
    if response.status_code in {429, 503}:
        raise CaptureError(
            f"Bing Search rate-limited or unavailable ({response.status_code})"
        )
    if response.status_code >= 400:
        raise CaptureError(
            f"Bing Search HTTP {response.status_code}: {response.text[:200]}"
        )
    try:
        payload = response.json()
    except ValueError as exc:
        raise CaptureError(f"Bing Search returned non-JSON body: {exc}") from exc
    if not isinstance(payload, dict):
        raise CaptureError("Bing Search JSON root must be an object")
    return payload, response.status_code


async def capture(
    bank_id: str,
    cohort_entry: CohortEntry,
    capture_date: date,
    *,
    queries: tuple[str, ...] | None = None,
) -> CaptureResult:
    """
    Measure non-branded Bing SERP visibility for the bank's domain.

    Returns CaptureResult with at most one WebMetric. Raises CaptureError on
    auth / rate-limit / hard API failures — never invents ranking shares.
    """
    raw_domain = (cohort_entry.domain or "").strip()
    if not raw_domain:
        return CaptureResult(
            bank_id=bank_id,
            capture_date=capture_date,
            attempted_platforms=[],
            errors=["bing_serp: no domain configured for this bank"],
        )

    try:
        domain = normalize_domain(raw_domain)
    except ValueError as exc:
        return CaptureResult(
            bank_id=bank_id,
            capture_date=capture_date,
            attempted_platforms=[Platform.WEBSITE],
            errors=[f"bing_serp: {exc}"],
        )

    api_key = _get_api_key()
    if not api_key:
        raise CaptureError("BING_SEARCH_API_KEY is not set")

    query_set = queries if queries is not None else NON_BRANDED_QUERIES
    if not query_set:
        return CaptureResult(
            bank_id=bank_id,
            capture_date=capture_date,
            attempted_platforms=[Platform.WEBSITE],
            errors=["bing_serp: empty query set"],
        )

    attempted_platforms = [Platform.WEBSITE]
    errors: list[str] = []
    fetched_at = datetime.now(timezone.utc)
    rate_limit = get_rate_limit_seconds()

    raw_by_query: dict[str, Any] = {}
    urls_by_query: dict[str, list[str]] = {}
    last_status = 200

    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        for index, query in enumerate(query_set):
            if index > 0:
                await asyncio.sleep(rate_limit)
            try:
                payload, http_status = await _fetch_query(client, api_key, query)
            except CaptureError:
                raise
            except httpx.HTTPError as exc:
                raise CaptureError(f"Bing Search HTTP error for {query!r}: {exc}") from exc

            last_status = http_status
            raw_by_query[query] = payload
            urls = extract_organic_urls(payload)
            urls_by_query[query] = urls
            if not urls:
                errors.append(f"bing_serp: no organic results for query {query!r}")

    artifact_path = _raw_artifact_path(bank_id, capture_date)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_payload = {
        "domain": domain,
        "queries": list(query_set),
        "responses": raw_by_query,
    }
    artifact_path.write_text(json.dumps(artifact_payload, indent=2), encoding="utf-8")
    raw_artifacts = {
        "bing_serp": str(artifact_path.relative_to(REPO_ROOT)),
    }

    ranking_keywords, share, top_keywords = score_query_hits(urls_by_query, domain)

    web_metrics = [
        WebMetric(
            bank_id=bank_id,
            capture_date=capture_date,
            ranking_keywords=ranking_keywords,
            non_branded_search_share=share,
            top_keywords=top_keywords,
            source=SourceProvenance(
                url=BING_SEARCH_API,
                fetched_at=fetched_at,
                http_status=last_status,
                method="api",
            ),
        )
    ]

    return CaptureResult(
        bank_id=bank_id,
        capture_date=capture_date,
        web_metrics=web_metrics,
        raw_artifacts=raw_artifacts,
        errors=errors,
        attempted_platforms=attempted_platforms,
    )

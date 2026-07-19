"""Similarweb free-tier website overview — traffic estimates and top keywords.

Fetches the public (unauthenticated) data endpoint historically exposed at
``https://data.similarweb.com/api/v1/data?domain=…``. Metrics map into
``WebMetric``; fields Similarweb does not expose (authority score, backlinks,
branded share) stay ``None``.

When CloudFront / WAF blocks the free endpoint (HTTP 403/429 or HTML challenge
body), raises ``CaptureError`` — never substitutes synthetic traffic figures.
"""
from __future__ import annotations

import json
import re
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

SIMILARWEB_DATA_API = "https://data.similarweb.com/api/v1/data"
SIMILARWEB_OVERVIEW_URL = "https://www.similarweb.com/website/{domain}/"


def normalize_domain(domain: str) -> str:
    """Strip scheme, path, and leading www. for the Similarweb domain param."""
    value = domain.strip().lower()
    value = re.sub(r"^https?://", "", value)
    value = value.split("/")[0]
    if value.startswith("www."):
        value = value[4:]
    if not value or "." not in value:
        raise ValueError(f"invalid domain: {domain!r}")
    return value


def overview_url(domain: str) -> str:
    """Public Similarweb overview URL used for provenance."""
    return SIMILARWEB_OVERVIEW_URL.format(domain=normalize_domain(domain))


def _parse_int(raw: Any) -> Optional[int]:
    if raw is None:
        return None
    if isinstance(raw, bool):
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


def _parse_share(raw: Any) -> Optional[float]:
    """Return a traffic-source share clamped to [0, 1], or None."""
    if raw is None:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value < 0 or value > 1:
        return None
    return value


def latest_monthly_visits(estimated: dict[str, Any] | None) -> Optional[int]:
    """Pick the most recent month from EstimatedMonthlyVisits."""
    if not estimated:
        return None
    best_key: Optional[str] = None
    best_value: Optional[int] = None
    for key, raw in estimated.items():
        visits = _parse_int(raw)
        if visits is None:
            continue
        if best_key is None or str(key) > best_key:
            best_key = str(key)
            best_value = visits
    return best_value


def extract_top_keywords(payload: dict[str, Any], *, limit: int = 10) -> list[str]:
    """Return up to ``limit`` keyword name strings from TopKeywords."""
    raw_keywords = payload.get("TopKeywords") or []
    names: list[str] = []
    for item in raw_keywords:
        if not isinstance(item, dict):
            continue
        name = item.get("Name") or item.get("name")
        if isinstance(name, str) and name.strip():
            names.append(name.strip())
        if len(names) >= limit:
            break
    return names


def parse_similarweb_payload(payload: dict[str, Any]) -> tuple[Optional[int], list[str], list[str]]:
    """Derive (organic_traffic_est, top_keywords, soft_errors) from API JSON.

    organic_traffic_est = latest monthly visits × Search traffic share when both
    are present. If Search share is missing, organic stays None (we refuse to
    relabel total visits as organic).
    """
    errors: list[str] = []
    top_keywords = extract_top_keywords(payload)

    visits = latest_monthly_visits(payload.get("EstimatedMonthlyVisits"))
    if visits is None:
        engagements = payload.get("Engagments") or payload.get("Engagements") or {}
        visits = _parse_int(engagements.get("Visits"))

    sources = payload.get("TrafficSources") or {}
    search_share = _parse_share(sources.get("Search"))

    organic: Optional[int] = None
    if visits is not None and search_share is not None:
        organic = int(round(visits * search_share))
    elif visits is not None and search_share is None:
        errors.append(
            "similarweb: total visits present but Search share missing; "
            "organic_traffic_est left as None"
        )
    else:
        errors.append("similarweb: no visit estimate in payload")

    if not top_keywords:
        errors.append("similarweb: no top keywords in payload")

    return organic, top_keywords, errors


def _looks_like_block_page(status_code: int, body: str, content_type: str) -> bool:
    if status_code in {401, 403, 429, 503}:
        return True
    lowered = body[:2000].lower()
    if "text/html" in content_type.lower() and (
        "cloudfront" in lowered
        or "request blocked" in lowered
        or "aws waf" in lowered
        or "gokuprops" in lowered
    ):
        return True
    return False


def _raw_artifact_path(bank_id: str, capture_date: date) -> Path:
    return (
        INTELLIGENCE_DATA_DIR
        / "raw"
        / capture_date.isoformat()
        / bank_id
        / "similarweb_overview.json"
    )


async def _fetch_overview(
    client: httpx.AsyncClient,
    domain: str,
) -> tuple[dict[str, Any], int, str]:
    """GET the free data API; return (json, http_status, request_url)."""
    request_url = f"{SIMILARWEB_DATA_API}?domain={domain}"
    response = await client.get(SIMILARWEB_DATA_API, params={"domain": domain})
    content_type = response.headers.get("content-type", "")
    body = response.text

    if _looks_like_block_page(response.status_code, body, content_type):
        raise CaptureError(
            f"Similarweb free endpoint blocked or unavailable "
            f"({response.status_code}) for domain={domain}"
        )
    if response.status_code >= 400:
        raise CaptureError(
            f"Similarweb HTTP {response.status_code} for domain={domain}: "
            f"{body[:200]}"
        )
    try:
        payload = response.json()
    except ValueError as exc:
        raise CaptureError(
            f"Similarweb returned non-JSON body for domain={domain}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise CaptureError(
            f"Similarweb JSON root must be an object for domain={domain}"
        )
    return payload, response.status_code, request_url


async def capture(
    bank_id: str,
    cohort_entry: CohortEntry,
    capture_date: date,
) -> CaptureResult:
    """
    Pull free-tier website traffic / keyword snapshot for the bank domain.

    Returns CaptureResult with at most one WebMetric. Raises CaptureError on
    rate-limit, WAF, or hard HTTP failures — never invents traffic numbers.
    """
    raw_domain = (cohort_entry.domain or "").strip()
    if not raw_domain:
        return CaptureResult(
            bank_id=bank_id,
            capture_date=capture_date,
            attempted_platforms=[],
            errors=["similarweb: no domain configured for this bank"],
        )

    try:
        domain = normalize_domain(raw_domain)
    except ValueError as exc:
        return CaptureResult(
            bank_id=bank_id,
            capture_date=capture_date,
            attempted_platforms=[Platform.WEBSITE],
            errors=[f"similarweb: {exc}"],
        )

    attempted_platforms = [Platform.WEBSITE]
    errors: list[str] = []
    web_metrics: list[WebMetric] = []
    raw_artifacts: dict[str, str] = {}
    fetched_at = datetime.now(timezone.utc)

    headers = {
        "User-Agent": get_user_agent(),
        "Accept": "application/json",
    }
    async with httpx.AsyncClient(headers=headers, timeout=60.0, follow_redirects=True) as client:
        try:
            payload, http_status, _request_url = await _fetch_overview(client, domain)
        except CaptureError:
            raise
        except httpx.HTTPError as exc:
            raise CaptureError(f"Similarweb HTTP error for {domain}: {exc}") from exc

    artifact_path = _raw_artifact_path(bank_id, capture_date)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    raw_artifacts["similarweb_overview"] = str(artifact_path.relative_to(REPO_ROOT))

    organic, top_keywords, parse_errors = parse_similarweb_payload(payload)
    errors.extend(parse_errors)

    # Always record a WebMetric row when the API returned JSON — provenance
    # survives even if organic/keywords could not be parsed.
    web_metrics.append(
        WebMetric(
            bank_id=bank_id,
            capture_date=capture_date,
            organic_traffic_est=organic,
            top_keywords=top_keywords,
            ranking_keywords=len(top_keywords) if top_keywords else None,
            source=SourceProvenance(
                url=overview_url(domain),
                fetched_at=fetched_at,
                http_status=http_status,
                method="api",
            ),
        )
    )

    return CaptureResult(
        bank_id=bank_id,
        capture_date=capture_date,
        web_metrics=web_metrics,
        raw_artifacts=raw_artifacts,
        errors=errors,
        attempted_platforms=attempted_platforms,
    )

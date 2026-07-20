"""Ahrefs free Website Authority / Backlink Checker capture.

Fetches the public Ahrefs free-tool pages (no login) for a bank domain and
parses Domain Rating, backlink, and referring-domain signals when present in
the HTML. Metrics that only render client-side stay ``None`` — never invented.

Maps into ``WebMetric``:
- ``authority_score`` ← Domain Rating (0–100)
- ``backlinks`` ← backlink count
- ``referring_domains`` ← referring domain count
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
from ingestion.intelligence.web.similarweb import normalize_domain

AUTHORITY_CHECKER_URL = "https://ahrefs.com/website-authority-checker/?input={domain}"
BACKLINK_CHECKER_URL = (
    "https://ahrefs.com/backlink-checker/?input={domain}&mode=subdomains"
)

_DOMAIN_RATING_JSON_RE = re.compile(
    r'"domain[_ ]?rating"\s*:\s*(\d{1,3})',
    re.IGNORECASE,
)
_BACKLINKS_JSON_RE = re.compile(
    r'"(?:backlinks|backLinks|totalBacklinks)"\s*:\s*(\d+)',
    re.IGNORECASE,
)
_REFDOMAINS_JSON_RE = re.compile(
    r'"(?:refdomains|refDomains|referring_domains|referringDomains)"\s*:\s*(\d+)',
    re.IGNORECASE,
)
# Require the number immediately after the label (optional colon/dash).
# Looser "within N chars" patterns false-positive on Ahrefs CSS class digits
# near the marketing "Domain Rating" SVG alt text.
_DOMAIN_RATING_TEXT_RE = re.compile(
    r"Domain\s*Rating\s*[:\-]?\s*(\d{1,3})\b",
    re.IGNORECASE,
)
_BACKLINKS_TEXT_RE = re.compile(
    r"\b([\d,]+)\s+backlinks?\b",
    re.IGNORECASE,
)
_REFDOMAINS_TEXT_RE = re.compile(
    r"\b([\d,]+)\s+referring\s+domains?\b",
    re.IGNORECASE,
)


def authority_checker_url(domain: str) -> str:
    return AUTHORITY_CHECKER_URL.format(domain=normalize_domain(domain))


def backlink_checker_url(domain: str) -> str:
    return BACKLINK_CHECKER_URL.format(domain=normalize_domain(domain))


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


def parse_ahrefs_metrics(html: str) -> tuple[Optional[int], Optional[int], Optional[int], list[str]]:
    """Return (authority_score, backlinks, referring_domains, soft_errors)."""
    errors: list[str] = []

    authority: Optional[int] = None
    for pattern in (_DOMAIN_RATING_JSON_RE, _DOMAIN_RATING_TEXT_RE):
        match = pattern.search(html)
        if match:
            authority = _parse_int(match.group(1))
            if authority is not None and authority > 100:
                authority = None
                continue
            break

    backlinks: Optional[int] = None
    for pattern in (_BACKLINKS_JSON_RE, _BACKLINKS_TEXT_RE):
        match = pattern.search(html)
        if match:
            backlinks = _parse_int(match.group(1))
            if backlinks is not None:
                break

    referring: Optional[int] = None
    for pattern in (_REFDOMAINS_JSON_RE, _REFDOMAINS_TEXT_RE):
        match = pattern.search(html)
        if match:
            referring = _parse_int(match.group(1))
            if referring is not None:
                break

    if authority is None and backlinks is None and referring is None:
        errors.append(
            "ahrefs_free: no Domain Rating / backlinks / referring domains "
            "found in free-tool HTML (metrics may be client-rendered only)"
        )
    else:
        if authority is None:
            errors.append("ahrefs_free: Domain Rating not found in HTML")
        if backlinks is None:
            errors.append("ahrefs_free: backlink count not found in HTML")
        if referring is None:
            errors.append("ahrefs_free: referring domains not found in HTML")

    return authority, backlinks, referring, errors


def merge_ahrefs_metrics(
    *parsed: tuple[Optional[int], Optional[int], Optional[int], list[str]],
) -> tuple[Optional[int], Optional[int], Optional[int], list[str]]:
    """Prefer the first non-None value per field across free-tool page parses."""
    authority: Optional[int] = None
    backlinks: Optional[int] = None
    referring: Optional[int] = None
    errors: list[str] = []
    for auth, backs, refs, errs in parsed:
        if authority is None:
            authority = auth
        if backlinks is None:
            backlinks = backs
        if referring is None:
            referring = refs
        errors.extend(errs)
    if authority is not None or backlinks is not None or referring is not None:
        # Drop the all-null soft error once any page yielded a metric.
        errors = [
            err
            for err in errors
            if "client-rendered only" not in err
            and not err.endswith("not found in HTML")
        ]
        if authority is None:
            errors.append("ahrefs_free: Domain Rating not found in HTML")
        if backlinks is None:
            errors.append("ahrefs_free: backlink count not found in HTML")
        if referring is None:
            errors.append("ahrefs_free: referring domains not found in HTML")
    else:
        # Keep a single client-rendered note when every page was empty.
        errors = [
            "ahrefs_free: no Domain Rating / backlinks / referring domains "
            "found in free-tool HTML (metrics may be client-rendered only)"
        ]
    return authority, backlinks, referring, errors


def _raw_artifact_path(bank_id: str, capture_date: date, filename: str) -> Path:
    return (
        INTELLIGENCE_DATA_DIR
        / "raw"
        / capture_date.isoformat()
        / bank_id
        / filename
    )


async def _fetch_html(client: httpx.AsyncClient, url: str) -> tuple[str, int, str]:
    response = await client.get(url, follow_redirects=True)
    if response.status_code in {429, 503}:
        raise CaptureError(
            f"Ahrefs free tool rate-limited or unavailable ({response.status_code})"
        )
    if response.status_code in {401, 403}:
        raise CaptureError(
            f"Ahrefs free tool blocked or unauthorized ({response.status_code})"
        )
    if response.status_code >= 400:
        raise CaptureError(f"Ahrefs free tool HTTP {response.status_code} for {url}")
    return response.text, response.status_code, str(response.url)


async def capture(
    bank_id: str,
    cohort_entry: CohortEntry,
    capture_date: date,
) -> CaptureResult:
    """
    Pull Ahrefs free-tool authority / backlink signals for the bank domain.

    Fetches both the Website Authority Checker and Backlink Checker public
    pages and merges whatever metrics are present in static HTML. Client-only
    rendered values stay ``None`` — never invented.

    Returns CaptureResult with at most one WebMetric. Raises CaptureError on
    rate-limit / hard HTTP failures.
    """
    raw_domain = (cohort_entry.domain or "").strip()
    if not raw_domain:
        return CaptureResult(
            bank_id=bank_id,
            capture_date=capture_date,
            attempted_platforms=[],
            errors=["ahrefs_free: no domain configured for this bank"],
        )

    try:
        domain = normalize_domain(raw_domain)
    except ValueError as exc:
        return CaptureResult(
            bank_id=bank_id,
            capture_date=capture_date,
            attempted_platforms=[Platform.WEBSITE],
            errors=[f"ahrefs_free: {exc}"],
        )

    attempted_platforms = [Platform.WEBSITE]
    fetched_at = datetime.now(timezone.utc)
    authority_url = authority_checker_url(domain)
    backlink_url = backlink_checker_url(domain)

    headers = {
        "User-Agent": get_user_agent(),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }
    async with httpx.AsyncClient(headers=headers, timeout=60.0) as client:
        try:
            authority_html, http_status, final_url = await _fetch_html(
                client, authority_url
            )
            backlink_html, _, backlink_final = await _fetch_html(client, backlink_url)
        except CaptureError:
            raise
        except httpx.HTTPError as exc:
            raise CaptureError(f"Ahrefs free tool HTTP error: {exc}") from exc

    artifact_path = _raw_artifact_path(bank_id, capture_date, "ahrefs_free.html")
    backlink_artifact = _raw_artifact_path(
        bank_id, capture_date, "ahrefs_free_backlinks.html"
    )
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(authority_html, encoding="utf-8")
    backlink_artifact.write_text(backlink_html, encoding="utf-8")

    authority, backlinks, referring, errors = merge_ahrefs_metrics(
        parse_ahrefs_metrics(authority_html),
        parse_ahrefs_metrics(backlink_html),
    )
    summary_path = artifact_path.with_suffix(".json")
    summary_path.write_text(
        json.dumps(
            {
                "domain": domain,
                "source_url": final_url,
                "backlink_checker_url": backlink_final,
                "authority_score": authority,
                "backlinks": backlinks,
                "referring_domains": referring,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    raw_artifacts = {
        "ahrefs_free": str(artifact_path.relative_to(REPO_ROOT)),
        "ahrefs_free_backlinks": str(backlink_artifact.relative_to(REPO_ROOT)),
        "ahrefs_free_summary": str(summary_path.relative_to(REPO_ROOT)),
    }

    web_metrics = [
        WebMetric(
            bank_id=bank_id,
            capture_date=capture_date,
            authority_score=authority,
            backlinks=backlinks,
            referring_domains=referring,
            source=SourceProvenance(
                url=final_url,
                fetched_at=fetched_at,
                http_status=http_status,
                method="scrape",
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

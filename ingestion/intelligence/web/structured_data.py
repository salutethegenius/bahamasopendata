"""Schema.org structured data detection on bank websites.

Fetches the public homepage HTML (no login) and detects JSON-LD and microdata
``schema.org`` types. Emits one ``WebMetric`` where:

- ``top_keywords`` ← detected ``@type`` / itemtype local names
- ``ranking_keywords`` ← count of distinct types

Absence of structured data is a valid measurement (empty ``top_keywords``),
not a synthetic failure.
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

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

_SCHEMA_HOSTS = ("schema.org", "www.schema.org")


def homepage_url(domain: str) -> str:
    return f"https://{normalize_domain(domain)}/"


def _local_type_name(raw: str) -> Optional[str]:
    value = raw.strip()
    if not value:
        return None
    if value.startswith("http://") or value.startswith("https://"):
        parsed = urlparse(value)
        if parsed.netloc.lower() not in _SCHEMA_HOSTS:
            return None
        value = parsed.path.rstrip("/").split("/")[-1]
    return value or None


def _collect_types_from_jsonld(node: Any, into: set[str]) -> None:
    if isinstance(node, dict):
        type_value = node.get("@type")
        if isinstance(type_value, str):
            name = _local_type_name(type_value)
            if name:
                into.add(name)
        elif isinstance(type_value, list):
            for item in type_value:
                if isinstance(item, str):
                    name = _local_type_name(item)
                    if name:
                        into.add(name)
        for value in node.values():
            _collect_types_from_jsonld(value, into)
    elif isinstance(node, list):
        for item in node:
            _collect_types_from_jsonld(item, into)


def _loads_jsonld(raw: str) -> Any | None:
    """Parse JSON-LD text; tolerate UTF-8 BOM and trailing commas in objects."""
    cleaned = raw.strip().lstrip("\ufeff")
    if not cleaned:
        return None
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # Some CMS exports leave a trailing comma before } or ].
    repaired = re.sub(r",\s*([}\]])", r"\1", cleaned)
    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        return None


def extract_jsonld_types(html: str) -> list[str]:
    """Return sorted unique schema.org types from JSON-LD script tags."""
    soup = BeautifulSoup(html, "html.parser")
    found: set[str] = set()
    for script in soup.find_all("script"):
        script_type = (script.get("type") or "").lower().replace(" ", "")
        if "ld+json" not in script_type:
            continue
        raw = script.string or script.get_text() or ""
        payload = _loads_jsonld(raw)
        if payload is None:
            continue
        _collect_types_from_jsonld(payload, found)
    return sorted(found)


def extract_microdata_types(html: str) -> list[str]:
    """Return sorted unique schema.org types from microdata itemtype attrs."""
    soup = BeautifulSoup(html, "html.parser")
    found: set[str] = set()
    for element in soup.find_all(attrs={"itemtype": True}):
        raw = element.get("itemtype")
        if not isinstance(raw, str):
            continue
        for token in re.split(r"\s+", raw.strip()):
            name = _local_type_name(token)
            if name:
                found.add(name)
    return sorted(found)


def extract_rdfa_types(html: str) -> list[str]:
    """Return sorted unique schema.org types from RDFa typeof attrs."""
    soup = BeautifulSoup(html, "html.parser")
    found: set[str] = set()
    for element in soup.find_all(attrs={"typeof": True}):
        raw = element.get("typeof")
        if not isinstance(raw, str):
            continue
        for token in re.split(r"\s+", raw.strip()):
            # RDFa often uses compact IRIs like schema:Organization.
            if ":" in token and not token.startswith("http"):
                prefix, local = token.split(":", 1)
                if prefix.lower() in {"schema", "schema.org"}:
                    name = _local_type_name(local)
                    if name:
                        found.add(name)
                continue
            name = _local_type_name(token)
            if name:
                found.add(name)
    return sorted(found)


def detect_schema_types(html: str) -> tuple[list[str], list[str]]:
    """Return (types, soft_errors) combining JSON-LD, microdata, and RDFa."""
    errors: list[str] = []
    types = sorted(
        set(
            extract_jsonld_types(html)
            + extract_microdata_types(html)
            + extract_rdfa_types(html)
        )
    )
    if not types:
        # Absence is a valid measurement — soft note, never invent types.
        errors.append(
            "structured_data: no schema.org types detected on homepage "
            "(JSON-LD / microdata / RDFa)"
        )
    return types, errors


def _raw_artifact_path(bank_id: str, capture_date: date) -> Path:
    return (
        INTELLIGENCE_DATA_DIR
        / "raw"
        / capture_date.isoformat()
        / bank_id
        / "structured_data.html"
    )


async def _fetch_homepage(
    client: httpx.AsyncClient,
    url: str,
) -> tuple[str, int, str]:
    response = await client.get(url, follow_redirects=True)
    if response.status_code in {429, 503}:
        raise CaptureError(
            f"Homepage rate-limited or unavailable ({response.status_code}) for {url}"
        )
    if response.status_code in {401, 403}:
        raise CaptureError(
            f"Homepage auth wall or blocked ({response.status_code}) for {url}"
        )
    if response.status_code >= 400:
        raise CaptureError(f"Homepage HTTP {response.status_code} for {url}")
    return response.text, response.status_code, str(response.url)


async def capture(
    bank_id: str,
    cohort_entry: CohortEntry,
    capture_date: date,
) -> CaptureResult:
    """
    Detect schema.org structured data on the bank homepage.

    Returns CaptureResult with at most one WebMetric. Raises CaptureError on
    rate-limit / hard HTTP failures — never invents schema types.
    """
    raw_domain = (cohort_entry.domain or "").strip()
    if not raw_domain:
        return CaptureResult(
            bank_id=bank_id,
            capture_date=capture_date,
            attempted_platforms=[],
            errors=["structured_data: no domain configured for this bank"],
        )

    try:
        page_url = homepage_url(raw_domain)
    except ValueError as exc:
        return CaptureResult(
            bank_id=bank_id,
            capture_date=capture_date,
            attempted_platforms=[Platform.WEBSITE],
            errors=[f"structured_data: {exc}"],
        )

    attempted_platforms = [Platform.WEBSITE]
    errors: list[str] = []
    fetched_at = datetime.now(timezone.utc)

    headers = {
        "User-Agent": get_user_agent(),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }
    async with httpx.AsyncClient(headers=headers, timeout=60.0) as client:
        try:
            html, http_status, final_url = await _fetch_homepage(client, page_url)
        except CaptureError:
            raise
        except httpx.HTTPError as exc:
            raise CaptureError(f"Homepage HTTP error for {page_url}: {exc}") from exc

    artifact_path = _raw_artifact_path(bank_id, capture_date)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(html, encoding="utf-8")

    types, parse_errors = detect_schema_types(html)
    errors.extend(parse_errors)

    web_metrics = [
        WebMetric(
            bank_id=bank_id,
            capture_date=capture_date,
            ranking_keywords=len(types) if types else 0,
            top_keywords=types,
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
        raw_artifacts={
            "structured_data": str(artifact_path.relative_to(REPO_ROOT)),
        },
        errors=errors,
        attempted_platforms=attempted_platforms,
    )

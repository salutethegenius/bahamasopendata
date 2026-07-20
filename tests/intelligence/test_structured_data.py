"""Tests for ingestion.intelligence.web.structured_data."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import httpx
import pytest

from ingestion.intelligence.cohort import CohortEntry, CohortSocial
from ingestion.intelligence.errors import CaptureError
from ingestion.intelligence.types import Platform
from ingestion.intelligence.web import structured_data

FIXTURES = Path(__file__).resolve().parent / "fixtures"
CAPTURE_DATE = date(2026, 8, 15)


def _cohort_entry(domain: str | None = "combankltd.com") -> CohortEntry:
    return CohortEntry(
        id="commonwealth_bank",
        legal_name="Commonwealth Bank Limited",
        display_name="Commonwealth Bank",
        short_name="Commonwealth",
        series_token="--intel-series-3",
        domain=domain,
        social=CohortSocial(),
    )


def test_detect_schema_types_from_fixture():
    html = (FIXTURES / "structured_data.html").read_text()
    types, errors = structured_data.detect_schema_types(html)
    assert types == ["BankOrCreditUnion", "FinancialService", "Organization"]
    assert errors == []


def test_detect_schema_types_empty():
    types, errors = structured_data.detect_schema_types("<html><body>hi</body></html>")
    assert types == []
    assert any("no schema.org" in err for err in errors)


def test_extract_rdfa_and_trailing_comma_jsonld():
    html = """
    <script type="application/ld+json">
    {"@type": "BankOrCreditUnion", "name": "X",}
    </script>
    <div typeof="schema:ATM"></div>
    """
    assert "BankOrCreditUnion" in structured_data.extract_jsonld_types(html)
    assert structured_data.extract_rdfa_types(html) == ["ATM"]


@pytest.mark.asyncio
async def test_capture_returns_web_metric(monkeypatch, tmp_path):
    html = (FIXTURES / "structured_data.html").read_text()
    monkeypatch.setattr(
        structured_data, "INTELLIGENCE_DATA_DIR", tmp_path / "data" / "intelligence"
    )
    monkeypatch.setattr(structured_data, "REPO_ROOT", tmp_path)

    async def fake_fetch(client, url):
        return html, 200, url

    monkeypatch.setattr(structured_data, "_fetch_homepage", fake_fetch)

    result = await structured_data.capture(
        "commonwealth_bank", _cohort_entry(), CAPTURE_DATE
    )

    assert result.attempted_platforms == [Platform.WEBSITE]
    metric = result.web_metrics[0]
    assert metric.ranking_keywords == 3
    assert metric.top_keywords == [
        "BankOrCreditUnion",
        "FinancialService",
        "Organization",
    ]
    assert metric.source.method == "scrape"
    assert "structured_data" in result.raw_artifacts


@pytest.mark.asyncio
async def test_capture_no_domain_soft_error():
    result = await structured_data.capture(
        "commonwealth_bank", _cohort_entry(None), CAPTURE_DATE
    )
    assert result.web_metrics == []
    assert "no domain configured" in result.errors[0]


@pytest.mark.asyncio
async def test_fetch_homepage_raises_on_503():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="down")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(CaptureError, match="503"):
            await structured_data._fetch_homepage(client, "https://combankltd.com/")

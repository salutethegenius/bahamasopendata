"""Tests for ingestion.intelligence.web.pagespeed."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import httpx
import pytest

from ingestion.intelligence.cohort import CohortEntry, CohortSocial
from ingestion.intelligence.errors import CaptureError
from ingestion.intelligence.types import Platform
from ingestion.intelligence.web import pagespeed

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


def test_homepage_url():
    assert pagespeed.homepage_url("combankltd.com") == "https://www.combankltd.com/"


def test_parse_lighthouse_categories():
    payload = json.loads((FIXTURES / "pagespeed_response.json").read_text())
    performance, labels, errors = pagespeed.parse_lighthouse_categories(payload)
    assert performance == 85
    assert "performance:85" in labels
    assert "seo:90" in labels
    assert any("Lighthouse performance" in err for err in errors)


@pytest.mark.asyncio
async def test_capture_returns_web_metric(monkeypatch, tmp_path):
    payload = json.loads((FIXTURES / "pagespeed_response.json").read_text())
    monkeypatch.setattr(
        pagespeed, "INTELLIGENCE_DATA_DIR", tmp_path / "data" / "intelligence"
    )
    monkeypatch.setattr(pagespeed, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(pagespeed, "_get_api_key", lambda: "test-key")

    async def fake_fetch(client, api_key, page_url):
        assert api_key == "test-key"
        assert page_url == "https://www.combankltd.com/"
        return payload, 200

    monkeypatch.setattr(pagespeed, "_fetch_pagespeed", fake_fetch)

    result = await pagespeed.capture(
        "commonwealth_bank", _cohort_entry(), CAPTURE_DATE
    )

    assert result.attempted_platforms == [Platform.WEBSITE]
    metric = result.web_metrics[0]
    assert metric.authority_score == 85
    assert metric.ranking_keywords == 4
    assert metric.source.method == "api"
    assert "pagespeed" in result.raw_artifacts


@pytest.mark.asyncio
async def test_capture_missing_key_raises(monkeypatch):
    monkeypatch.setattr(pagespeed, "_get_api_key", lambda: "")
    with pytest.raises(CaptureError, match="PAGESPEED_API_KEY"):
        await pagespeed.capture("commonwealth_bank", _cohort_entry(), CAPTURE_DATE)


@pytest.mark.asyncio
async def test_fetch_pagespeed_raises_on_429():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="quota")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(CaptureError, match="429"):
            await pagespeed._fetch_pagespeed(
                client, "key", "https://www.combankltd.com/"
            )

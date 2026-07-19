"""Tests for ingestion.intelligence.web.similarweb."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import httpx
import pytest

from ingestion.intelligence.cohort import CohortEntry, CohortSocial
from ingestion.intelligence.errors import CaptureError
from ingestion.intelligence.types import Platform
from ingestion.intelligence.web import similarweb

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


def test_normalize_domain_strips_scheme_www_and_path():
    assert similarweb.normalize_domain("https://www.ComBankLtd.com/login") == "combankltd.com"
    assert similarweb.normalize_domain("bs.scotiabank.com") == "bs.scotiabank.com"


def test_normalize_domain_rejects_invalid():
    with pytest.raises(ValueError, match="invalid domain"):
        similarweb.normalize_domain("notaurl")


def test_overview_url():
    assert (
        similarweb.overview_url("combankltd.com")
        == "https://www.similarweb.com/website/combankltd.com/"
    )


def test_latest_monthly_visits_picks_newest_month():
    visits = similarweb.latest_monthly_visits(
        {"2026-05-01": 45000, "2026-07-01": 52000, "2026-06-01": 48000}
    )
    assert visits == 52000


def test_parse_similarweb_payload_computes_organic_and_keywords():
    payload = json.loads((FIXTURES / "similarweb_overview.json").read_text())
    organic, keywords, errors = similarweb.parse_similarweb_payload(payload)
    assert organic == 18200  # round(52000 * 0.35)
    assert keywords == [
        "commonwealth bank bahamas",
        "combank online",
        "bahamas banking",
    ]
    assert errors == []


def test_parse_similarweb_payload_leaves_organic_none_without_search_share():
    payload = {
        "EstimatedMonthlyVisits": {"2026-07-01": 1000},
        "TrafficSources": {"Direct": 1.0},
        "TopKeywords": [],
    }
    organic, keywords, errors = similarweb.parse_similarweb_payload(payload)
    assert organic is None
    assert keywords == []
    assert any("Search share missing" in err for err in errors)
    assert any("no top keywords" in err for err in errors)


@pytest.mark.asyncio
async def test_capture_returns_web_metric_with_provenance(monkeypatch, tmp_path):
    payload = json.loads((FIXTURES / "similarweb_overview.json").read_text())
    monkeypatch.setattr(
        similarweb, "INTELLIGENCE_DATA_DIR", tmp_path / "data" / "intelligence"
    )
    monkeypatch.setattr(similarweb, "REPO_ROOT", tmp_path)

    async def fake_fetch(client, domain):
        assert domain == "combankltd.com"
        return payload, 200, "https://data.similarweb.com/api/v1/data?domain=combankltd.com"

    monkeypatch.setattr(similarweb, "_fetch_overview", fake_fetch)

    result = await similarweb.capture(
        "commonwealth_bank", _cohort_entry(), CAPTURE_DATE
    )

    assert result.attempted_platforms == [Platform.WEBSITE]
    assert len(result.web_metrics) == 1
    metric = result.web_metrics[0]
    assert metric.organic_traffic_est == 18200
    assert metric.ranking_keywords == 3
    assert metric.top_keywords[0] == "commonwealth bank bahamas"
    assert metric.source.method == "api"
    assert metric.source.http_status == 200
    assert "similarweb.com/website/combankltd.com" in str(metric.source.url)
    assert "similarweb_overview" in result.raw_artifacts
    assert result.errors == []


@pytest.mark.asyncio
async def test_capture_no_domain_soft_error():
    result = await similarweb.capture(
        "commonwealth_bank", _cohort_entry(None), CAPTURE_DATE
    )
    assert result.web_metrics == []
    assert result.attempted_platforms == []
    assert "no domain configured" in result.errors[0]


@pytest.mark.asyncio
async def test_capture_raises_on_block(monkeypatch, tmp_path):
    monkeypatch.setattr(
        similarweb, "INTELLIGENCE_DATA_DIR", tmp_path / "data" / "intelligence"
    )
    monkeypatch.setattr(similarweb, "REPO_ROOT", tmp_path)

    async def blocked(*args, **kwargs):
        raise CaptureError(
            "Similarweb free endpoint blocked or unavailable (403) for domain=combankltd.com"
        )

    monkeypatch.setattr(similarweb, "_fetch_overview", blocked)

    with pytest.raises(CaptureError, match="blocked"):
        await similarweb.capture("commonwealth_bank", _cohort_entry(), CAPTURE_DATE)


@pytest.mark.asyncio
async def test_fetch_overview_detects_cloudfront_403():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            headers={"content-type": "text/html"},
            text="<html>ERROR: The request could not be satisfied. CloudFront Request blocked.</html>",
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(CaptureError, match="blocked"):
            await similarweb._fetch_overview(client, "combankltd.com")

"""Tests for ingestion.intelligence.web.bing_serp."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import httpx
import pytest

from ingestion.intelligence.cohort import CohortEntry, CohortSocial
from ingestion.intelligence.errors import CaptureError
from ingestion.intelligence.types import Platform
from ingestion.intelligence.web import bing_serp

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


def test_normalize_domain():
    assert bing_serp.normalize_domain("https://www.ComBankLtd.com/x") == "combankltd.com"


def test_host_matches_domain():
    assert bing_serp.host_matches_domain(
        "https://www.combankltd.com/personal", "combankltd.com"
    )
    assert bing_serp.host_matches_domain(
        "https://online.combankltd.com/", "combankltd.com"
    )
    assert not bing_serp.host_matches_domain(
        "https://example.com/combankltd.com", "combankltd.com"
    )


def test_extract_organic_urls():
    payload = json.loads((FIXTURES / "bing_serp_response.json").read_text())
    urls = bing_serp.extract_organic_urls(payload)
    assert urls[0] == "https://www.combankltd.com/personal/bank-accounts"
    assert len(urls) == 3


def test_score_query_hits():
    ranking, share, hits = bing_serp.score_query_hits(
        {
            "bank account bahamas": [
                "https://www.combankltd.com/a",
                "https://example.com",
            ],
            "mortgage rates bahamas": ["https://example.com"],
            "online banking bahamas": ["https://online.combankltd.com/login"],
        },
        "combankltd.com",
    )
    assert ranking == 2
    assert share == pytest.approx(2 / 3)
    assert hits == ["bank account bahamas", "online banking bahamas"]


@pytest.mark.asyncio
async def test_capture_returns_web_metric(monkeypatch, tmp_path):
    payload = json.loads((FIXTURES / "bing_serp_response.json").read_text())
    empty = {"webPages": {"value": []}}
    monkeypatch.setattr(
        bing_serp, "INTELLIGENCE_DATA_DIR", tmp_path / "data" / "intelligence"
    )
    monkeypatch.setattr(bing_serp, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(bing_serp, "_get_api_key", lambda: "test-key")
    monkeypatch.setattr(bing_serp, "get_rate_limit_seconds", lambda: 0)

    calls: list[str] = []

    async def fake_fetch(client, api_key, query):
        calls.append(query)
        if query == "bank account bahamas":
            return payload, 200
        return empty, 200

    monkeypatch.setattr(bing_serp, "_fetch_query", fake_fetch)

    result = await bing_serp.capture(
        "commonwealth_bank",
        _cohort_entry(),
        CAPTURE_DATE,
        queries=("bank account bahamas", "mortgage rates bahamas"),
    )

    assert calls == ["bank account bahamas", "mortgage rates bahamas"]
    assert result.attempted_platforms == [Platform.WEBSITE]
    assert len(result.web_metrics) == 1
    metric = result.web_metrics[0]
    assert metric.ranking_keywords == 1
    assert metric.non_branded_search_share == pytest.approx(0.5)
    assert metric.top_keywords == ["bank account bahamas"]
    assert metric.source.method == "api"
    assert "bing_serp" in result.raw_artifacts
    assert any("no organic results" in err for err in result.errors)


@pytest.mark.asyncio
async def test_capture_no_domain_soft_error():
    result = await bing_serp.capture(
        "commonwealth_bank", _cohort_entry(None), CAPTURE_DATE
    )
    assert result.web_metrics == []
    assert result.attempted_platforms == []
    assert "no domain configured" in result.errors[0]


@pytest.mark.asyncio
async def test_capture_missing_api_key_raises(monkeypatch):
    monkeypatch.setattr(bing_serp, "_get_api_key", lambda: "")
    with pytest.raises(CaptureError, match="BING_SEARCH_API_KEY"):
        await bing_serp.capture(
            "commonwealth_bank", _cohort_entry(), CAPTURE_DATE, queries=("x",)
        )


@pytest.mark.asyncio
async def test_fetch_query_raises_on_401():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="unauthorized")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(CaptureError, match="401"):
            await bing_serp._fetch_query(client, "bad-key", "bank account bahamas")

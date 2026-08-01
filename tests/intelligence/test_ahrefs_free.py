"""Tests for ingestion.intelligence.web.ahrefs_free."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import httpx
import pytest

from ingestion.intelligence.cohort import CohortEntry, CohortSocial
from ingestion.intelligence.errors import CaptureError
from ingestion.intelligence.types import Platform
from ingestion.intelligence.web import ahrefs_free

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


def test_authority_checker_url():
    assert "website-authority-checker" in ahrefs_free.authority_checker_url(
        "combankltd.com"
    )


def test_parse_ahrefs_metrics_from_fixture():
    html = (FIXTURES / "ahrefs_free.html").read_text()
    authority, backlinks, referring, errors = ahrefs_free.parse_ahrefs_metrics(html)
    assert authority == 42
    assert backlinks == 1234
    assert referring == 56
    assert errors == []


def test_parse_ahrefs_metrics_empty():
    authority, backlinks, referring, errors = ahrefs_free.parse_ahrefs_metrics(
        "<html><body>no metrics</body></html>"
    )
    assert authority is None
    assert backlinks is None
    assert referring is None
    assert any("client-rendered" in err for err in errors)


def test_merge_ahrefs_metrics_prefers_non_null():
    empty = ahrefs_free.parse_ahrefs_metrics("<html></html>")
    filled = ahrefs_free.parse_ahrefs_metrics(
        (FIXTURES / "ahrefs_free.html").read_text()
    )
    authority, backlinks, referring, errors = ahrefs_free.merge_ahrefs_metrics(
        empty, filled
    )
    assert authority == 42
    assert backlinks == 1234
    assert referring == 56
    assert not any("client-rendered" in err for err in errors)


@pytest.mark.asyncio
async def test_capture_returns_web_metric(monkeypatch, tmp_path):
    html = (FIXTURES / "ahrefs_free.html").read_text()
    monkeypatch.setattr(
        ahrefs_free, "INTELLIGENCE_DATA_DIR", tmp_path / "data" / "intelligence"
    )
    monkeypatch.setattr(ahrefs_free, "REPO_ROOT", tmp_path)

    fetched: list[str] = []

    async def fake_fetch(client, url):
        fetched.append(url)
        return html, 200, url

    monkeypatch.setattr(ahrefs_free, "_fetch_html", fake_fetch)

    result = await ahrefs_free.capture(
        "commonwealth_bank", _cohort_entry(), CAPTURE_DATE
    )

    assert len(fetched) == 2
    assert any("website-authority-checker" in url for url in fetched)
    assert any("backlink-checker" in url for url in fetched)
    assert result.attempted_platforms == [Platform.WEBSITE]
    metric = result.web_metrics[0]
    assert metric.authority_score == 42
    assert metric.backlinks == 1234
    assert metric.referring_domains == 56
    assert metric.source.method == "scrape"
    assert "ahrefs_free" in result.raw_artifacts
    assert "ahrefs_free_backlinks" in result.raw_artifacts


@pytest.mark.asyncio
async def test_capture_no_domain_soft_error():
    result = await ahrefs_free.capture(
        "commonwealth_bank", _cohort_entry(None), CAPTURE_DATE
    )
    assert result.web_metrics == []
    assert "no domain configured" in result.errors[0]


@pytest.mark.asyncio
async def test_fetch_html_raises_on_403():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, text="blocked")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(CaptureError, match="403"):
            await ahrefs_free._fetch_html(
                client, "https://ahrefs.com/website-authority-checker/?input=x.com"
            )

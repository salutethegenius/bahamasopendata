"""Tests for ingestion.intelligence.social.tiktok."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import httpx
import pytest

from ingestion.intelligence.cohort import CohortEntry, CohortSocial
from ingestion.intelligence.errors import CaptureError
from ingestion.intelligence.social import tiktok
from ingestion.intelligence.types import Platform

FIXTURES = Path(__file__).resolve().parent / "fixtures"
CAPTURE_DATE = date(2026, 8, 15)


def _cohort_entry(handle: str | None = "nba") -> CohortEntry:
    return CohortEntry(
        id="rbc_bahamas",
        legal_name="RBC Royal Bank (Bahamas) Limited",
        display_name="RBC Royal Bank Bahamas",
        short_name="RBC Bahamas",
        series_token="--intel-series-1",
        social=CohortSocial(tiktok=handle),
    )


def test_normalize_handle_strips_at_and_url():
    assert tiktok.normalize_handle("@nba") == "nba"
    assert tiktok.normalize_handle("https://www.tiktok.com/@nba") == "nba"


def test_normalize_handle_rejects_invalid():
    with pytest.raises(ValueError, match="invalid tiktok handle"):
        tiktok.normalize_handle("bad handle!")


def test_profile_url():
    assert tiktok.profile_url("nba") == "https://www.tiktok.com/@nba"


def test_parse_compact_count():
    assert tiktok.parse_compact_count("50.2M") == 50_200_000
    assert tiktok.parse_compact_count("2,289") == 2289


def test_parse_profile_counts_prefers_rehydration_json():
    html = (FIXTURES / "tiktok_profile.html").read_text()
    followers, errors = tiktok.parse_profile_counts(html)
    assert followers == 50_200_000
    assert errors == []


def test_parse_profile_counts_from_og_when_no_json():
    html = (
        '<meta property="og:description" '
        'content="Bank (@bank) on TikTok · 12.5K Followers, 10 Following, 1 Likes" />'
    )
    followers, errors = tiktok.parse_profile_counts(html)
    assert followers == 12_500
    assert errors == []


def test_looks_like_waf_challenge():
    html = (FIXTURES / "tiktok_waf_challenge.html").read_text()
    assert tiktok.looks_like_waf_challenge(html) is True
    assert tiktok.looks_like_waf_challenge(
        (FIXTURES / "tiktok_profile.html").read_text()
    ) is False


@pytest.mark.asyncio
async def test_capture_returns_social_metric_with_provenance(monkeypatch, tmp_path):
    html = (FIXTURES / "tiktok_profile.html").read_text()
    monkeypatch.setattr(
        tiktok, "INTELLIGENCE_DATA_DIR", tmp_path / "data" / "intelligence"
    )
    monkeypatch.setattr(tiktok, "REPO_ROOT", tmp_path)

    async def fake_fetch(client, handle):
        assert handle == "nba"
        return html, 200, "https://www.tiktok.com/@nba"

    monkeypatch.setattr(tiktok, "_fetch_profile_html", fake_fetch)

    result = await tiktok.capture("rbc_bahamas", _cohort_entry("nba"), CAPTURE_DATE)

    assert result.attempted_platforms == [Platform.TIKTOK]
    assert len(result.social_metrics) == 1
    metric = result.social_metrics[0]
    assert metric.platform == Platform.TIKTOK
    assert metric.followers == 50_200_000
    assert metric.source.method == "scrape"
    assert "tiktok_profile" in result.raw_artifacts
    assert result.errors == []


@pytest.mark.asyncio
async def test_capture_no_handle_soft_error():
    result = await tiktok.capture("rbc_bahamas", _cohort_entry(None), CAPTURE_DATE)
    assert result.social_metrics == []
    assert result.attempted_platforms == []
    assert "no handle configured" in result.errors[0]


@pytest.mark.asyncio
async def test_capture_raises_on_waf(monkeypatch, tmp_path):
    monkeypatch.setattr(
        tiktok, "INTELLIGENCE_DATA_DIR", tmp_path / "data" / "intelligence"
    )
    monkeypatch.setattr(tiktok, "REPO_ROOT", tmp_path)

    async def waf(*args, **kwargs):
        raise CaptureError("TikTok WAF challenge blocked public scrape for @nba")

    monkeypatch.setattr(tiktok, "_fetch_profile_html", waf)

    with pytest.raises(CaptureError, match="WAF"):
        await tiktok.capture("rbc_bahamas", _cohort_entry("nba"), CAPTURE_DATE)


@pytest.mark.asyncio
async def test_fetch_profile_html_detects_waf_body():
    html = (FIXTURES / "tiktok_waf_challenge.html").read_text()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=html)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(CaptureError, match="WAF"):
            await tiktok._fetch_profile_html(client, "nba")

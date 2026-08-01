"""Tests for ingestion.intelligence.social.facebook."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import httpx
import pytest

from ingestion.intelligence.cohort import CohortEntry, CohortSocial
from ingestion.intelligence.errors import CaptureError
from ingestion.intelligence.social import facebook
from ingestion.intelligence.types import Platform

FIXTURES = Path(__file__).resolve().parent / "fixtures"
CAPTURE_DATE = date(2026, 8, 15)


def _cohort_entry(handle: str | None = "CommonwealthBank242") -> CohortEntry:
    return CohortEntry(
        id="commonwealth_bank",
        legal_name="Commonwealth Bank Limited",
        display_name="Commonwealth Bank",
        short_name="Commonwealth",
        series_token="--intel-series-3",
        social=CohortSocial(facebook=handle),
    )


def test_normalize_handle_strips_url():
    assert facebook.normalize_handle("CommonwealthBank242") == "CommonwealthBank242"
    assert (
        facebook.normalize_handle("https://www.facebook.com/CommonwealthBank242/")
        == "CommonwealthBank242"
    )


def test_normalize_handle_rejects_invalid():
    with pytest.raises(ValueError, match="invalid facebook handle"):
        facebook.normalize_handle("bad handle!")


def test_page_url():
    assert (
        facebook.page_url("RBCCaribbean")
        == "https://www.facebook.com/RBCCaribbean/"
    )


def test_parse_compact_count():
    assert facebook.parse_compact_count("6,649") == 6649
    assert facebook.parse_compact_count("6.6K") == 6600


def test_parse_page_counts_prefers_exact_likes_over_compact_followers():
    html = (FIXTURES / "facebook_profile.html").read_text()
    followers, errors = facebook.parse_page_counts(html)
    # Exact 6,649 likes beats compacted 6.6K followers.
    assert followers == 6649
    assert any("exact page likes" in err for err in errors)


def test_parse_page_counts_falls_back_to_likes():
    html = (FIXTURES / "facebook_profile_likes_only.html").read_text()
    followers, errors = facebook.parse_page_counts(html)
    assert followers == 14601
    assert any("likes" in err and "proxy" in err for err in errors)


def test_parse_page_counts_uses_compact_followers_when_no_exact_likes():
    html = '<script>var payload = {"text":"6.6K followers"};</script>'
    followers, errors = facebook.parse_page_counts(html)
    assert followers == 6600
    assert errors == []


def test_parse_page_counts_missing():
    followers, errors = facebook.parse_page_counts("<html><body>hi</body></html>")
    assert followers is None
    assert any("no follower or likes" in err for err in errors)


@pytest.mark.asyncio
async def test_capture_returns_social_metric_with_provenance(monkeypatch, tmp_path):
    html = (FIXTURES / "facebook_profile.html").read_text()
    monkeypatch.setattr(
        facebook, "INTELLIGENCE_DATA_DIR", tmp_path / "data" / "intelligence"
    )
    monkeypatch.setattr(facebook, "REPO_ROOT", tmp_path)

    async def fake_fetch(client, handle):
        assert handle == "CommonwealthBank242"
        return html, 200, "https://www.facebook.com/CommonwealthBank242/"

    monkeypatch.setattr(facebook, "_fetch_page_html", fake_fetch)

    result = await facebook.capture(
        "commonwealth_bank", _cohort_entry(), CAPTURE_DATE
    )

    assert result.attempted_platforms == [Platform.FACEBOOK]
    assert len(result.social_metrics) == 1
    metric = result.social_metrics[0]
    assert metric.platform == Platform.FACEBOOK
    assert metric.followers == 6649
    assert metric.source.method == "scrape"
    assert metric.source.http_status == 200
    assert "facebook_profile" in result.raw_artifacts
    assert any("exact page likes" in err for err in result.errors)


@pytest.mark.asyncio
async def test_capture_no_handle_soft_error():
    result = await facebook.capture(
        "commonwealth_bank", _cohort_entry(None), CAPTURE_DATE
    )
    assert result.social_metrics == []
    assert result.attempted_platforms == []
    assert "no handle configured" in result.errors[0]


@pytest.mark.asyncio
async def test_capture_raises_on_rate_limit(monkeypatch, tmp_path):
    monkeypatch.setattr(
        facebook, "INTELLIGENCE_DATA_DIR", tmp_path / "data" / "intelligence"
    )
    monkeypatch.setattr(facebook, "REPO_ROOT", tmp_path)

    async def limited(*args, **kwargs):
        raise CaptureError("Facebook rate-limited or unavailable (429) for x")

    monkeypatch.setattr(facebook, "_fetch_page_html", limited)

    with pytest.raises(CaptureError, match="rate-limited"):
        await facebook.capture("commonwealth_bank", _cohort_entry(), CAPTURE_DATE)


@pytest.mark.asyncio
async def test_fetch_page_html_raises_on_429():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="slow down")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(CaptureError, match="429"):
            await facebook._fetch_page_html(client, "CommonwealthBank242")

"""Tests for ingestion.intelligence.social.instagram."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import httpx
import pytest

from ingestion.intelligence.cohort import CohortEntry, CohortSocial
from ingestion.intelligence.errors import CaptureError
from ingestion.intelligence.social import instagram
from ingestion.intelligence.types import Platform

FIXTURES = Path(__file__).resolve().parent / "fixtures"
CAPTURE_DATE = date(2026, 8, 15)


def _cohort_entry(handle: str | None = "commonwealthbankltd") -> CohortEntry:
    return CohortEntry(
        id="commonwealth_bank",
        legal_name="Commonwealth Bank Limited",
        display_name="Commonwealth Bank",
        short_name="Commonwealth",
        series_token="--intel-series-3",
        social=CohortSocial(instagram=handle),
    )


def test_normalize_handle_strips_at_and_url():
    assert instagram.normalize_handle("@commonwealthbankltd") == "commonwealthbankltd"
    assert (
        instagram.normalize_handle("https://www.instagram.com/commonwealthbankltd/")
        == "commonwealthbankltd"
    )


def test_normalize_handle_rejects_invalid():
    with pytest.raises(ValueError, match="invalid instagram handle"):
        instagram.normalize_handle("bad handle!")


def test_profile_url():
    assert (
        instagram.profile_url("@rbc")
        == "https://www.instagram.com/rbc/"
    )


def test_parse_compact_count():
    assert instagram.parse_compact_count("2,289") == 2289
    assert instagram.parse_compact_count("1.2K") == 1200
    assert instagram.parse_compact_count("3M") == 3_000_000


def test_parse_profile_counts_from_fixture():
    html = (FIXTURES / "instagram_profile.html").read_text()
    followers, posts, errors = instagram.parse_profile_counts(html)
    assert followers == 2289
    assert posts == 861
    assert errors == []


def test_parse_profile_counts_missing_meta():
    followers, posts, errors = instagram.parse_profile_counts("<html><body>hi</body></html>")
    assert followers is None
    assert posts is None
    assert any("no follower meta" in err for err in errors)


@pytest.mark.asyncio
async def test_capture_returns_social_metric_with_provenance(monkeypatch, tmp_path):
    html = (FIXTURES / "instagram_profile.html").read_text()
    monkeypatch.setattr(
        instagram, "INTELLIGENCE_DATA_DIR", tmp_path / "data" / "intelligence"
    )
    monkeypatch.setattr(instagram, "REPO_ROOT", tmp_path)

    async def fake_fetch(client, handle):
        assert handle == "commonwealthbankltd"
        return html, 200, "https://www.instagram.com/commonwealthbankltd/"

    monkeypatch.setattr(instagram, "_fetch_profile_html", fake_fetch)

    result = await instagram.capture(
        "commonwealth_bank", _cohort_entry(), CAPTURE_DATE
    )

    assert result.attempted_platforms == [Platform.INSTAGRAM]
    assert len(result.social_metrics) == 1
    metric = result.social_metrics[0]
    assert metric.platform == Platform.INSTAGRAM
    assert metric.followers == 2289
    assert metric.posts_in_window is None
    assert metric.source.method == "scrape"
    assert metric.source.http_status == 200
    assert "instagram_profile" in result.raw_artifacts
    assert any("lifetime posts" in err for err in result.errors)


@pytest.mark.asyncio
async def test_capture_no_handle_soft_error():
    result = await instagram.capture(
        "commonwealth_bank", _cohort_entry(None), CAPTURE_DATE
    )
    assert result.social_metrics == []
    assert result.attempted_platforms == []
    assert "no handle configured" in result.errors[0]


@pytest.mark.asyncio
async def test_capture_raises_on_rate_limit(monkeypatch, tmp_path):
    monkeypatch.setattr(
        instagram, "INTELLIGENCE_DATA_DIR", tmp_path / "data" / "intelligence"
    )
    monkeypatch.setattr(instagram, "REPO_ROOT", tmp_path)

    async def limited(*args, **kwargs):
        raise CaptureError("Instagram rate-limited or unavailable (429) for @x")

    monkeypatch.setattr(instagram, "_fetch_profile_html", limited)

    with pytest.raises(CaptureError, match="rate-limited"):
        await instagram.capture("commonwealth_bank", _cohort_entry(), CAPTURE_DATE)


@pytest.mark.asyncio
async def test_fetch_profile_html_raises_on_429():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="slow down")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(CaptureError, match="429"):
            await instagram._fetch_profile_html(client, "commonwealthbankltd")

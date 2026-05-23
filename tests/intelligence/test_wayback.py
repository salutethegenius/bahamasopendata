"""Tests for ingestion.intelligence.social.wayback (reference scraper contract)."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import httpx
import pytest

from ingestion.intelligence.cohort import CohortEntry, CohortSocial
from ingestion.intelligence.errors import CaptureError
from ingestion.intelligence.social import wayback
from ingestion.intelligence.types import Platform

FIXTURES = Path(__file__).resolve().parent / "fixtures"
CAPTURE_DATE = date(2026, 8, 15)
SEED_URL = "https://www.facebook.com/RBCRoyalBankBahamas"


def _cohort_entry() -> CohortEntry:
    return CohortEntry(
        id="rbc_bahamas",
        legal_name="RBC Royal Bank (Bahamas) Limited",
        display_name="RBC Royal Bank Bahamas",
        short_name="RBC Bahamas",
        series_token="--intel-series-1",
        wayback_seeds=[SEED_URL],
    )


def test_platform_for_url():
    assert wayback._platform_for_url(SEED_URL) == Platform.FACEBOOK
    assert wayback._platform_for_url("https://www.instagram.com/rbc") == Platform.INSTAGRAM


def test_parse_follower_count_facebook():
    html = (FIXTURES / "wayback_facebook_snapshot.html").read_text()
    assert wayback._parse_follower_count(html, Platform.FACEBOOK) == 12345


def test_pick_nearest_cdx_timestamp_selects_closest_in_window():
    rows = [
        ["urlkey", "timestamp", "original", "mimetype", "statuscode"],
        ["fb", "20260808120000", SEED_URL, "text/html", "200"],
        ["fb", "20260820120000", SEED_URL, "text/html", "200"],
    ]
    selected = wayback._pick_nearest_cdx_timestamp(rows, CAPTURE_DATE)
    assert selected == "20260820120000"


def test_pick_nearest_cdx_timestamp_prefers_exact_day_when_present():
    rows = [
        ["urlkey", "timestamp", "original", "mimetype", "statuscode"],
        ["fb", "20260808120000", SEED_URL, "text/html", "200"],
        ["fb", "20260815143000", SEED_URL, "text/html", "200"],
        ["fb", "20260820120000", SEED_URL, "text/html", "200"],
    ]
    selected = wayback._pick_nearest_cdx_timestamp(rows, CAPTURE_DATE)
    assert selected == "20260815143000"


def test_cdx_window_bounds_span_seven_days():
    start, end = wayback._cdx_window_bounds(CAPTURE_DATE)
    assert start == "20260808"
    assert end == "20260822"


@pytest.mark.asyncio
async def test_capture_returns_social_metric_with_provenance(monkeypatch, tmp_path):
    html = (FIXTURES / "wayback_facebook_snapshot.html").read_text()
    raw_root = tmp_path / "data" / "intelligence" / "raw"
    monkeypatch.setattr(wayback, "INTELLIGENCE_DATA_DIR", tmp_path / "data" / "intelligence")
    monkeypatch.setattr(wayback, "REPO_ROOT", tmp_path)

    async def fake_cdx(client, seed_url, capture_date):
        assert seed_url == SEED_URL
        return "20260815120000"

    async def fake_snapshot(client, seed_url, timestamp):
        return (
            html,
            f"https://web.archive.org/web/{timestamp}/{seed_url}",
            200,
        )

    monkeypatch.setattr(wayback, "_fetch_cdx_timestamp", fake_cdx)
    monkeypatch.setattr(wayback, "_fetch_snapshot_html", fake_snapshot)
    monkeypatch.setattr(wayback, "get_rate_limit_seconds", lambda: 0)

    result = await wayback.capture("rbc_bahamas", _cohort_entry(), CAPTURE_DATE)

    assert result.bank_id == "rbc_bahamas"
    assert len(result.social_metrics) == 1
    metric = result.social_metrics[0]
    assert metric.platform == Platform.FACEBOOK
    assert metric.followers == 12345
    assert metric.source.method == "wayback"
    assert metric.source.archive_url is not None
    assert str(metric.source.archive_url).startswith("https://web.archive.org/")
    assert "wayback_facebook" in result.raw_artifacts
    assert result.attempted_platforms == [Platform.FACEBOOK]


def test_attempted_platforms_from_seeds_reflects_handles_present():
    entry = CohortEntry(
        id="rbc_bahamas",
        legal_name="RBC Royal Bank (Bahamas) Limited",
        display_name="RBC Royal Bank Bahamas",
        short_name="RBC Bahamas",
        series_token="--intel-series-1",
        wayback_seeds=[
            "https://www.facebook.com/RBCRoyalBankBahamas",
            "https://www.instagram.com/rbc",
        ],
    )
    assert wayback._attempted_platforms_from_seeds(entry.wayback_seeds) == [
        Platform.FACEBOOK,
        Platform.INSTAGRAM,
    ]


@pytest.mark.asyncio
async def test_capture_records_error_when_no_snapshot(monkeypatch):
    async def fake_cdx(*args):
        return None

    monkeypatch.setattr(wayback, "_fetch_cdx_timestamp", fake_cdx)
    monkeypatch.setattr(wayback, "get_rate_limit_seconds", lambda: 0)

    result = await wayback.capture("rbc_bahamas", _cohort_entry(), CAPTURE_DATE)

    assert result.social_metrics == []
    assert result.attempted_platforms == [Platform.FACEBOOK]
    assert any("no snapshot within" in err for err in result.errors)


@pytest.mark.asyncio
async def test_capture_selects_nearest_snapshot_when_not_exact_date(monkeypatch, tmp_path):
    html = (FIXTURES / "wayback_facebook_snapshot.html").read_text()
    monkeypatch.setattr(wayback, "INTELLIGENCE_DATA_DIR", tmp_path / "data" / "intelligence")
    monkeypatch.setattr(wayback, "REPO_ROOT", tmp_path)

    async def fake_cdx(client, seed_url, capture_date):
        return "20260820120000"

    async def fake_snapshot(client, seed_url, timestamp):
        assert timestamp == "20260820120000"
        return (
            html,
            f"https://web.archive.org/web/{timestamp}/{seed_url}",
            200,
        )

    monkeypatch.setattr(wayback, "_fetch_cdx_timestamp", fake_cdx)
    monkeypatch.setattr(wayback, "_fetch_snapshot_html", fake_snapshot)
    monkeypatch.setattr(wayback, "get_rate_limit_seconds", lambda: 0)

    result = await wayback.capture("rbc_bahamas", _cohort_entry(), CAPTURE_DATE)

    assert len(result.social_metrics) == 1
    assert result.attempted_platforms == [Platform.FACEBOOK]
    assert "20260820" in str(result.social_metrics[0].source.archive_url)
    assert result.social_metrics[0].capture_date == CAPTURE_DATE


@pytest.mark.asyncio
async def test_capture_raises_capture_error_on_rate_limit(monkeypatch):
    async def rate_limited_cdx(client, seed_url, capture_date):
        response = httpx.Response(429)
        raise CaptureError("Wayback CDX rate-limited or unavailable (429)")

    monkeypatch.setattr(wayback, "_fetch_cdx_timestamp", rate_limited_cdx)
    monkeypatch.setattr(wayback, "get_rate_limit_seconds", lambda: 0)

    with pytest.raises(CaptureError):
        await wayback.capture("rbc_bahamas", _cohort_entry(), CAPTURE_DATE)


@pytest.mark.asyncio
async def test_capture_no_seeds_returns_error_message():
    entry = _cohort_entry()
    entry = entry.model_copy(update={"wayback_seeds": []})
    result = await wayback.capture("rbc_bahamas", entry, CAPTURE_DATE)
    assert "no wayback_seeds" in result.errors[0]
    assert result.attempted_platforms == []

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


@pytest.mark.asyncio
async def test_capture_records_error_when_no_snapshot(monkeypatch):
    async def fake_cdx(*args):
        return None

    monkeypatch.setattr(wayback, "_fetch_cdx_timestamp", fake_cdx)
    monkeypatch.setattr(wayback, "get_rate_limit_seconds", lambda: 0)

    result = await wayback.capture("rbc_bahamas", _cohort_entry(), CAPTURE_DATE)

    assert result.social_metrics == []
    assert any("no snapshot" in err for err in result.errors)


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

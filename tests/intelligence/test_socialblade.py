"""Tests for ingestion.intelligence.social.socialblade."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import httpx
import pytest

from ingestion.intelligence.cohort import CohortEntry, CohortSocial
from ingestion.intelligence.errors import CaptureError
from ingestion.intelligence.social import socialblade
from ingestion.intelligence.types import Platform

FIXTURES = Path(__file__).resolve().parent / "fixtures"
CAPTURE_DATE = date(2026, 8, 15)


def _cohort_entry(
    *,
    youtube: str | None = "UCCr-rdQ1xIrcAj0IiG2mo8g",
    tiktok: str | None = None,
) -> CohortEntry:
    return CohortEntry(
        id="scotiabank_bahamas",
        legal_name="Scotiabank (Bahamas) Limited",
        display_name="Scotiabank Bahamas",
        short_name="Scotiabank",
        series_token="--intel-series-2",
        social=CohortSocial(youtube=youtube, tiktok=tiktok),
    )


def test_normalize_youtube_channel_id():
    assert socialblade.normalize_youtube_target("UCCr-rdQ1xIrcAj0IiG2mo8g") == (
        "channel",
        "UCCr-rdQ1xIrcAj0IiG2mo8g",
    )


def test_normalize_youtube_handle():
    assert socialblade.normalize_youtube_target("@RBC") == ("handle", "RBC")
    assert socialblade.socialblade_youtube_url("@RBC").endswith("/youtube/handle/RBC")


def test_socialblade_tiktok_url():
    assert (
        socialblade.socialblade_tiktok_url("@nba")
        == "https://socialblade.com/tiktok/user/nba"
    )


def test_parse_youtube_counts_from_fixture():
    html = (FIXTURES / "socialblade_youtube.html").read_text()
    subscribers, views, errors = socialblade.parse_youtube_counts(html)
    assert subscribers == 1960
    assert errors == []
    # views may be absent in slim fixture
    assert views is None or views >= 0


def test_parse_tiktok_counts_from_fixture():
    html = (FIXTURES / "socialblade_tiktok.html").read_text()
    followers, errors = socialblade.parse_tiktok_counts(html)
    assert followers == 27_100_000
    assert errors == []


@pytest.mark.asyncio
async def test_capture_youtube_success(monkeypatch, tmp_path):
    html = (FIXTURES / "socialblade_youtube.html").read_text()
    monkeypatch.setattr(
        socialblade, "INTELLIGENCE_DATA_DIR", tmp_path / "data" / "intelligence"
    )
    monkeypatch.setattr(socialblade, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(socialblade, "get_rate_limit_seconds", lambda: 0)

    async def fake_fetch(client, url):
        assert "youtube/channel/" in url
        return html, 200, url

    monkeypatch.setattr(socialblade, "_fetch_html", fake_fetch)

    result = await socialblade.capture(
        "scotiabank_bahamas", _cohort_entry(), CAPTURE_DATE
    )

    assert result.attempted_platforms == [Platform.YOUTUBE]
    assert len(result.social_metrics) == 1
    metric = result.social_metrics[0]
    assert metric.platform == Platform.YOUTUBE
    assert metric.followers == 1960
    assert metric.source.method == "socialblade"
    assert "socialblade_youtube" in result.raw_artifacts


@pytest.mark.asyncio
async def test_capture_youtube_and_tiktok(monkeypatch, tmp_path):
    yt = (FIXTURES / "socialblade_youtube.html").read_text()
    tt = (FIXTURES / "socialblade_tiktok.html").read_text()
    monkeypatch.setattr(
        socialblade, "INTELLIGENCE_DATA_DIR", tmp_path / "data" / "intelligence"
    )
    monkeypatch.setattr(socialblade, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(socialblade, "get_rate_limit_seconds", lambda: 0)

    async def fake_fetch(client, url):
        if "tiktok" in url:
            return tt, 200, url
        return yt, 200, url

    monkeypatch.setattr(socialblade, "_fetch_html", fake_fetch)

    result = await socialblade.capture(
        "scotiabank_bahamas",
        _cohort_entry(youtube="@RBC", tiktok="nba"),
        CAPTURE_DATE,
    )

    assert result.attempted_platforms == [Platform.YOUTUBE, Platform.TIKTOK]
    assert {m.platform for m in result.social_metrics} == {
        Platform.YOUTUBE,
        Platform.TIKTOK,
    }


@pytest.mark.asyncio
async def test_capture_no_handles_soft_error():
    result = await socialblade.capture(
        "fidelity_bahamas",
        _cohort_entry(youtube=None, tiktok=None),
        CAPTURE_DATE,
    )
    assert result.social_metrics == []
    assert result.attempted_platforms == []
    assert "no youtube or tiktok" in result.errors[0]


@pytest.mark.asyncio
async def test_fetch_html_raises_on_429():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="slow down")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(CaptureError, match="429"):
            await socialblade._fetch_html(
                client, "https://socialblade.com/youtube/handle/rbc"
            )

"""Tests for ingestion.intelligence.social.youtube."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import httpx
import pytest

from ingestion.intelligence.cohort import CohortEntry, CohortSocial
from ingestion.intelligence.errors import CaptureError
from ingestion.intelligence.social import youtube
from ingestion.intelligence.types import Platform

FIXTURES = Path(__file__).resolve().parent / "fixtures"
CAPTURE_DATE = date(2026, 8, 15)


def _cohort_entry(youtube_handle: str | None = "@RBC") -> CohortEntry:
    return CohortEntry(
        id="rbc_bahamas",
        legal_name="RBC Royal Bank (Bahamas) Limited",
        display_name="RBC Royal Bank Bahamas",
        short_name="RBC Bahamas",
        series_token="--intel-series-1",
        social=CohortSocial(youtube=youtube_handle),
    )


def test_resolve_channel_lookup_handle_with_at():
    assert youtube.resolve_channel_lookup("@RBC") == {"forHandle": "RBC"}


def test_resolve_channel_lookup_handle_without_at():
    assert youtube.resolve_channel_lookup("RBC") == {"forHandle": "RBC"}


def test_resolve_channel_lookup_channel_id():
    channel_id = "UCCr-rdQ1xIrcAj0IiG2mo8g"
    assert youtube.resolve_channel_lookup(channel_id) == {"id": channel_id}


def test_public_channel_url():
    assert youtube.public_channel_url("@RBC") == "https://www.youtube.com/@RBC"
    assert (
        youtube.public_channel_url("UCCr-rdQ1xIrcAj0IiG2mo8g")
        == "https://www.youtube.com/channel/UCCr-rdQ1xIrcAj0IiG2mo8g"
    )


def test_parse_channel_statistics_success():
    payload = json.loads((FIXTURES / "youtube_channel_response.json").read_text())
    followers, views, errors = youtube.parse_channel_statistics(payload)
    assert followers == 89000
    assert views == 1234567
    assert errors == []


def test_parse_channel_statistics_hidden_subscribers():
    payload = json.loads((FIXTURES / "youtube_channel_hidden_subs.json").read_text())
    followers, views, errors = youtube.parse_channel_statistics(payload)
    assert followers is None
    assert views == 100
    assert any("hidden" in err for err in errors)


def test_parse_channel_statistics_empty_items():
    followers, views, errors = youtube.parse_channel_statistics({"items": []})
    assert followers is None
    assert views is None
    assert any("not found" in err for err in errors)


@pytest.mark.asyncio
async def test_capture_returns_social_metric_with_provenance(monkeypatch, tmp_path):
    payload = json.loads((FIXTURES / "youtube_channel_response.json").read_text())
    monkeypatch.setattr(youtube, "INTELLIGENCE_DATA_DIR", tmp_path / "data" / "intelligence")
    monkeypatch.setattr(youtube, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(youtube, "_get_api_key", lambda: "test-key")

    async def fake_fetch(client, api_key, lookup):
        assert api_key == "test-key"
        assert lookup == {"forHandle": "RBC"}
        return payload, 200, "https://www.googleapis.com/youtube/v3/channels?…"

    monkeypatch.setattr(youtube, "_fetch_channel", fake_fetch)

    result = await youtube.capture("rbc_bahamas", _cohort_entry("@RBC"), CAPTURE_DATE)

    assert result.bank_id == "rbc_bahamas"
    assert result.attempted_platforms == [Platform.YOUTUBE]
    assert len(result.social_metrics) == 1
    metric = result.social_metrics[0]
    assert metric.platform == Platform.YOUTUBE
    assert metric.followers == 89000
    assert metric.views == 1234567
    assert metric.source.method == "api"
    assert metric.source.http_status == 200
    assert str(metric.source.url).startswith("https://www.youtube.com/@RBC")
    assert "youtube_channel" in result.raw_artifacts
    artifact = tmp_path / result.raw_artifacts["youtube_channel"]
    assert artifact.exists()
    assert result.errors == []


@pytest.mark.asyncio
async def test_capture_channel_id_lookup(monkeypatch, tmp_path):
    payload = json.loads((FIXTURES / "youtube_channel_response.json").read_text())
    monkeypatch.setattr(youtube, "INTELLIGENCE_DATA_DIR", tmp_path / "data" / "intelligence")
    monkeypatch.setattr(youtube, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(youtube, "_get_api_key", lambda: "test-key")

    channel_id = "UCCr-rdQ1xIrcAj0IiG2mo8g"

    async def fake_fetch(client, api_key, lookup):
        assert lookup == {"id": channel_id}
        return payload, 200, "https://example.invalid"

    monkeypatch.setattr(youtube, "_fetch_channel", fake_fetch)

    result = await youtube.capture(
        "scotiabank_bahamas",
        _cohort_entry(channel_id),
        CAPTURE_DATE,
    )
    assert result.social_metrics[0].followers == 89000
    assert "channel/" in str(result.social_metrics[0].source.url)


@pytest.mark.asyncio
async def test_capture_no_handle_returns_soft_error():
    result = await youtube.capture("fidelity_bahamas", _cohort_entry(None), CAPTURE_DATE)
    assert result.social_metrics == []
    assert result.attempted_platforms == []
    assert "no handle configured" in result.errors[0]


@pytest.mark.asyncio
async def test_capture_missing_api_key_raises(monkeypatch):
    monkeypatch.setattr(youtube, "_get_api_key", lambda: "")
    with pytest.raises(CaptureError, match="YOUTUBE_API_KEY"):
        await youtube.capture("rbc_bahamas", _cohort_entry("@RBC"), CAPTURE_DATE)


@pytest.mark.asyncio
async def test_capture_raises_on_quota(monkeypatch, tmp_path):
    monkeypatch.setattr(youtube, "INTELLIGENCE_DATA_DIR", tmp_path / "data" / "intelligence")
    monkeypatch.setattr(youtube, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(youtube, "_get_api_key", lambda: "test-key")

    async def rate_limited(*args, **kwargs):
        raise CaptureError("YouTube API rate-limited, unauthorized, or unavailable (403)")

    monkeypatch.setattr(youtube, "_fetch_channel", rate_limited)

    with pytest.raises(CaptureError, match="rate-limited"):
        await youtube.capture("rbc_bahamas", _cohort_entry("@RBC"), CAPTURE_DATE)


@pytest.mark.asyncio
async def test_capture_hidden_subscribers_keeps_none(monkeypatch, tmp_path):
    payload = json.loads((FIXTURES / "youtube_channel_hidden_subs.json").read_text())
    monkeypatch.setattr(youtube, "INTELLIGENCE_DATA_DIR", tmp_path / "data" / "intelligence")
    monkeypatch.setattr(youtube, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(youtube, "_get_api_key", lambda: "test-key")

    async def fake_fetch(*args, **kwargs):
        return payload, 200, "https://example.invalid"

    monkeypatch.setattr(youtube, "_fetch_channel", fake_fetch)

    result = await youtube.capture("rbc_bahamas", _cohort_entry("@RBC"), CAPTURE_DATE)

    assert len(result.social_metrics) == 1
    assert result.social_metrics[0].followers is None
    assert result.social_metrics[0].views == 100
    assert any("hidden" in err for err in result.errors)


@pytest.mark.asyncio
async def test_fetch_channel_raises_capture_error_on_403(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, text='{"error":{"errors":[{"reason":"quotaExceeded"}]}}')

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(CaptureError, match="403"):
            await youtube._fetch_channel(
                client, "test-key", {"forHandle": "RBC"}
            )

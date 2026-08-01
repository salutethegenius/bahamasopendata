"""Tests for ingestion.intelligence.social.twitter."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from ingestion.intelligence.cohort import CohortEntry, CohortSocial
from ingestion.intelligence.errors import CaptureError
from ingestion.intelligence.social import twitter
from ingestion.intelligence.types import Platform

FIXTURES = Path(__file__).resolve().parent / "fixtures"
CAPTURE_DATE = date(2026, 8, 15)


def _cohort_entry(handle: str | None = "cibccaribbeanbs") -> CohortEntry:
    return CohortEntry(
        id="cibc_caribbean",
        legal_name="CIBC Caribbean Bank Limited",
        display_name="CIBC Caribbean",
        short_name="CIBC Caribbean",
        series_token="--intel-series-5",
        social=CohortSocial(twitter=handle),
    )


def test_normalize_handle():
    assert twitter.normalize_handle("@cibccaribbeanbs") == "cibccaribbeanbs"
    assert (
        twitter.normalize_handle("https://x.com/cibccaribbeanbs")
        == "cibccaribbeanbs"
    )


def test_profile_urls():
    assert twitter.profile_urls("cibccaribbeanbs") == [
        "https://x.com/cibccaribbeanbs",
        "https://twitter.com/cibccaribbeanbs",
    ]


def test_parse_profile_counts_from_fixture():
    html = (FIXTURES / "twitter_profile.html").read_text()
    followers, errors = twitter.parse_profile_counts(html)
    assert followers == 1234
    assert errors == []


def test_looks_like_js_shell():
    assert twitter.looks_like_js_shell(
        (FIXTURES / "twitter_js_shell.html").read_text()
    )
    assert not twitter.looks_like_js_shell(
        (FIXTURES / "twitter_profile.html").read_text()
    )


@pytest.mark.asyncio
async def test_capture_live_success(monkeypatch, tmp_path):
    html = (FIXTURES / "twitter_profile.html").read_text()
    monkeypatch.setattr(
        twitter, "INTELLIGENCE_DATA_DIR", tmp_path / "data" / "intelligence"
    )
    monkeypatch.setattr(twitter, "REPO_ROOT", tmp_path)

    async def fake_live(client, url):
        return html, 200, url

    monkeypatch.setattr(twitter, "_fetch_live_html", fake_live)

    result = await twitter.capture(
        "cibc_caribbean", _cohort_entry(), CAPTURE_DATE
    )

    assert result.attempted_platforms == [Platform.TWITTER]
    assert result.social_metrics[0].followers == 1234
    assert result.social_metrics[0].source.method == "scrape"
    assert "twitter_live" in result.raw_artifacts


@pytest.mark.asyncio
async def test_capture_falls_back_to_wayback(monkeypatch, tmp_path):
    shell = (FIXTURES / "twitter_js_shell.html").read_text()
    archived = (FIXTURES / "twitter_profile.html").read_text()
    monkeypatch.setattr(
        twitter, "INTELLIGENCE_DATA_DIR", tmp_path / "data" / "intelligence"
    )
    monkeypatch.setattr(twitter, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(twitter, "get_rate_limit_seconds", lambda: 0)

    async def fake_live(client, url):
        return shell, 200, url

    async def fake_wayback(client, handle, capture_date, bank_id):
        path = (
            tmp_path
            / "data"
            / "intelligence"
            / "raw"
            / capture_date.isoformat()
            / bank_id
            / "twitter_wayback.html"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(archived, encoding="utf-8")
        return (
            1234,
            "https://web.archive.org/web/20260815120000/https://twitter.com/cibccaribbeanbs",
            200,
            str(path.relative_to(tmp_path)),
            [],
        )

    monkeypatch.setattr(twitter, "_fetch_live_html", fake_live)
    monkeypatch.setattr(twitter, "_wayback_fallback", fake_wayback)

    result = await twitter.capture(
        "cibc_caribbean", _cohort_entry(), CAPTURE_DATE
    )

    assert result.social_metrics[0].followers == 1234
    assert result.social_metrics[0].source.method == "wayback"
    assert result.social_metrics[0].source.archive_url is not None
    assert "twitter_wayback" in result.raw_artifacts
    assert any("JS shell" in err for err in result.errors)


@pytest.mark.asyncio
async def test_capture_no_handle_soft_error():
    result = await twitter.capture(
        "cibc_caribbean", _cohort_entry(None), CAPTURE_DATE
    )
    assert result.social_metrics == []
    assert result.attempted_platforms == []
    assert "no handle configured" in result.errors[0]


@pytest.mark.asyncio
async def test_capture_raises_on_live_rate_limit(monkeypatch, tmp_path):
    monkeypatch.setattr(
        twitter, "INTELLIGENCE_DATA_DIR", tmp_path / "data" / "intelligence"
    )
    monkeypatch.setattr(twitter, "REPO_ROOT", tmp_path)

    async def limited(*args, **kwargs):
        raise CaptureError("Twitter/X rate-limited or unavailable (429)")

    monkeypatch.setattr(twitter, "_fetch_live_html", limited)

    with pytest.raises(CaptureError, match="429"):
        await twitter.capture("cibc_caribbean", _cohort_entry(), CAPTURE_DATE)

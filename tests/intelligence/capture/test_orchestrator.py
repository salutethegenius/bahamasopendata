"""Tests for ingestion.intelligence.capture.orchestrator (v0.2 §8 step 6)."""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from ingestion.intelligence.capture import orchestrator, registry
from ingestion.intelligence.cohort import CohortEntry
from ingestion.intelligence.errors import CaptureError
from ingestion.intelligence.types import CaptureResult, Platform, SocialMetric, SourceProvenance

CAPTURE_DATE = date(2026, 8, 15)
BANK_ID = "rbc_bahamas"
OTHER_BANK_ID = "scotiabank_bahamas"
UTC = timezone.utc


def _cohort_entry(bank_id: str = BANK_ID) -> CohortEntry:
    return CohortEntry(
        id=bank_id,
        legal_name="Test Bank Limited",
        display_name="Test Bank",
        short_name="Test",
        series_token="--intel-series-1",
        wayback_seeds=["https://www.facebook.com/example"],
    )


def _sample_result(
    *,
    bank_id: str = BANK_ID,
    capture_date: date = CAPTURE_DATE,
    artifact_key: str = "wayback_facebook",
    artifact_path: str = "data/intelligence/raw/2026-08-15/rbc_bahamas/wayback_facebook.html",
    error: str | None = None,
) -> CaptureResult:
    provenance = SourceProvenance(
        url="https://www.facebook.com/example",
        fetched_at=datetime(2026, 8, 15, 12, 0, 0, tzinfo=UTC),
        http_status=200,
        method="wayback",
    )
    return CaptureResult(
        bank_id=bank_id,
        capture_date=capture_date,
        social_metrics=[
            SocialMetric(
                bank_id=bank_id,
                platform=Platform.FACEBOOK,
                capture_date=capture_date,
                followers=100,
                source=provenance,
            )
        ],
        raw_artifacts={artifact_key: artifact_path},
        errors=[error] if error else [],
        attempted_platforms=[Platform.FACEBOOK],
    )


@pytest.fixture
def intelligence_dirs(tmp_path, monkeypatch):
    data_dir = tmp_path / "data" / "intelligence"
    monkeypatch.setattr(registry, "REGISTRY_FILE", data_dir / "registry.json")
    monkeypatch.setattr(registry, "INTELLIGENCE_DATA_DIR", data_dir)
    monkeypatch.setattr(orchestrator, "INTELLIGENCE_DATA_DIR", data_dir)
    monkeypatch.setattr(orchestrator, "REPO_ROOT", tmp_path)
    return data_dir


def test_merge_capture_results_combines_two_valid_results():
    first = _sample_result(
        artifact_key="wayback_facebook",
        artifact_path="data/intelligence/raw/2026-08-15/rbc_bahamas/wayback_facebook.html",
        error="soft failure a",
    )
    second = _sample_result(
        artifact_key="wayback_instagram",
        artifact_path="data/intelligence/raw/2026-08-15/rbc_bahamas/wayback_instagram.html",
        error="soft failure b",
    )
    second = second.model_copy(
        update={
            "attempted_platforms": [Platform.INSTAGRAM],
            "social_metrics": [
                SocialMetric(
                    bank_id=BANK_ID,
                    platform=Platform.INSTAGRAM,
                    capture_date=CAPTURE_DATE,
                    followers=200,
                    source=second.social_metrics[0].source,
                )
            ],
        }
    )

    merged = orchestrator.merge_capture_results([first, second])

    assert merged.bank_id == BANK_ID
    assert merged.capture_date == CAPTURE_DATE
    assert len(merged.social_metrics) == 2
    assert merged.attempted_platforms == [Platform.FACEBOOK, Platform.INSTAGRAM]
    assert merged.raw_artifacts == {
        "wayback_facebook": "data/intelligence/raw/2026-08-15/rbc_bahamas/wayback_facebook.html",
        "wayback_instagram": "data/intelligence/raw/2026-08-15/rbc_bahamas/wayback_instagram.html",
    }
    assert merged.errors == ["soft failure a", "soft failure b"]


def test_merge_capture_results_raises_on_bank_id_mismatch():
    other = _sample_result(bank_id=OTHER_BANK_ID)
    with pytest.raises(ValueError, match="bank_id mismatch"):
        orchestrator.merge_capture_results([_sample_result(), other])


def test_merge_capture_results_raises_on_capture_date_mismatch():
    other = _sample_result(capture_date=date(2026, 8, 20))
    with pytest.raises(ValueError, match="capture_date mismatch"):
        orchestrator.merge_capture_results([_sample_result(), other])


def test_merge_capture_results_raises_on_empty_list():
    with pytest.raises(ValueError, match="at least one"):
        orchestrator.merge_capture_results([])


def test_merge_capture_results_raises_on_raw_artifact_key_collision():
    first = _sample_result(
        artifact_key="profile_html",
        artifact_path="data/intelligence/raw/2026-08-15/rbc_bahamas/youtube_profile.html",
    )
    second = _sample_result(
        artifact_key="profile_html",
        artifact_path="data/intelligence/raw/2026-08-15/rbc_bahamas/similarweb_profile.html",
    )
    with pytest.raises(ValueError, match="raw_artifacts key collision: 'profile_html'"):
        orchestrator.merge_capture_results([first, second])


@pytest.mark.asyncio
async def test_capture_one_success_writes_processed_json_and_registry(
    intelligence_dirs, monkeypatch
):
    mock_capture = AsyncMock(return_value=_sample_result())
    monkeypatch.setattr(
        orchestrator,
        "SCRAPERS",
        {"wayback": mock_capture},
    )
    monkeypatch.setattr(
        orchestrator,
        "get_cohort_entry",
        lambda bank_id: _cohort_entry(bank_id),
    )

    result, status = await orchestrator.capture_one(BANK_ID, CAPTURE_DATE)

    assert status == "complete"
    assert result.bank_id == BANK_ID
    mock_capture.assert_awaited_once()

    processed_path = (
        intelligence_dirs / "processed" / "2026-08-15" / f"{BANK_ID}.json"
    )
    assert processed_path.exists()
    payload = json.loads(processed_path.read_text())
    assert payload["bank_id"] == BANK_ID
    assert len(payload["social_metrics"]) == 1

    loaded = registry.load_registry()
    assert len(loaded.captures) == 1
    row = loaded.captures[0]
    assert row.scrape_status == "complete"
    assert row.platforms_captured == ["facebook"]
    assert row.platforms_failed == []
    assert row.processed_path.endswith("rbc_bahamas.json")


@pytest.mark.asyncio
async def test_capture_one_capture_error_marks_failed(
    intelligence_dirs, monkeypatch
):
    mock_capture = AsyncMock(side_effect=CaptureError("rate limited"))
    monkeypatch.setattr(orchestrator, "SCRAPERS", {"wayback": mock_capture})
    monkeypatch.setattr(
        orchestrator,
        "get_cohort_entry",
        lambda bank_id: _cohort_entry(bank_id),
    )

    result, status = await orchestrator.capture_one(BANK_ID, CAPTURE_DATE)

    assert status == "failed"
    assert result.errors == ["rate limited"]

    loaded = registry.load_registry()
    row = loaded.captures[0]
    assert row.scrape_status == "failed"
    assert row.platforms_failed == []
    assert row.platforms_captured == []


@pytest.mark.asyncio
async def test_capture_one_partial_platform_failure(
    intelligence_dirs, monkeypatch
):
    provenance = SourceProvenance(
        url="https://www.facebook.com/example",
        fetched_at=datetime(2026, 8, 15, 12, 0, 0, tzinfo=UTC),
        http_status=200,
        method="wayback",
    )
    partial_result = CaptureResult(
        bank_id=BANK_ID,
        capture_date=CAPTURE_DATE,
        attempted_platforms=[Platform.FACEBOOK, Platform.INSTAGRAM, Platform.TWITTER],
        social_metrics=[
            SocialMetric(
                bank_id=BANK_ID,
                platform=Platform.FACEBOOK,
                capture_date=CAPTURE_DATE,
                followers=100,
                source=provenance,
            ),
            SocialMetric(
                bank_id=BANK_ID,
                platform=Platform.INSTAGRAM,
                capture_date=CAPTURE_DATE,
                followers=None,
                source=provenance.model_copy(
                    update={"url": "https://www.instagram.com/example"}
                ),
            ),
        ],
    )
    mock_capture = AsyncMock(return_value=partial_result)
    monkeypatch.setattr(orchestrator, "SCRAPERS", {"wayback": mock_capture})
    monkeypatch.setattr(
        orchestrator,
        "get_cohort_entry",
        lambda bank_id: _cohort_entry(bank_id),
    )

    _, status = await orchestrator.capture_one(BANK_ID, CAPTURE_DATE)

    assert status == "partial"
    row = registry.load_registry().captures[0]
    assert row.platforms_captured == ["facebook", "instagram"]
    assert row.platforms_failed == ["twitter"]


@pytest.mark.asyncio
async def test_capture_one_unexpected_exception_marks_failed(
    intelligence_dirs, monkeypatch
):
    mock_capture = AsyncMock(side_effect=RuntimeError("network down"))
    mock_logger = MagicMock()
    monkeypatch.setattr(orchestrator, "SCRAPERS", {"wayback": mock_capture})
    monkeypatch.setattr(orchestrator, "logger", mock_logger)
    monkeypatch.setattr(
        orchestrator,
        "get_cohort_entry",
        lambda bank_id: _cohort_entry(bank_id),
    )

    result, status = await orchestrator.capture_one(BANK_ID, CAPTURE_DATE)

    assert status == "failed"
    assert result.errors == ["network down"]
    mock_logger.exception.assert_called_once()

    loaded = registry.load_registry()
    assert loaded.captures[0].scrape_status == "failed"
    assert loaded.captures[0].platforms_captured == []
    assert loaded.captures[0].platforms_failed == []


@pytest.mark.asyncio
async def test_capture_run_iterates_two_banks(intelligence_dirs, monkeypatch):
    calls: list[str] = []

    async def fake_capture_one(bank_id, capture_date, scrapers=None):
        calls.append(bank_id)
        return _sample_result(bank_id=bank_id), "complete"

    monkeypatch.setattr(orchestrator, "capture_one", fake_capture_one)

    results, statuses = await orchestrator.capture_run(
        CAPTURE_DATE,
        bank_ids=[BANK_ID, OTHER_BANK_ID],
    )

    assert calls == [BANK_ID, OTHER_BANK_ID]
    assert len(results) == 2
    assert statuses == ["complete", "complete"]

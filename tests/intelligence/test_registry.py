"""Tests for ingestion.intelligence.capture.registry (architecture v0.2 §4)."""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from ingestion.intelligence.capture import registry
from ingestion.intelligence.capture.registry import (
    CaptureRecord,
    IntelligenceRegistry,
    make_capture_id,
    mark_capture,
    mark_validation,
)
from ingestion.intelligence.types import CaptureResult

UTC = timezone.utc
CAPTURE_DATE = date(2026, 8, 15)
BANK_ID = "rbc_bahamas"


@pytest.fixture
def registry_file(tmp_path, monkeypatch):
    path = tmp_path / "registry.json"
    monkeypatch.setattr(registry, "REGISTRY_FILE", path)
    return path


def test_load_registry_missing_file_returns_empty(registry_file):
    loaded = registry.load_registry()
    assert loaded.captures == []


def test_save_and_load_round_trip(registry_file):
    record = CaptureRecord(
        capture_id=make_capture_id(BANK_ID, CAPTURE_DATE),
        bank_id=BANK_ID,
        capture_date=CAPTURE_DATE,
        platforms_captured=["facebook"],
        scrape_status="complete",
    )
    registry.save_registry(IntelligenceRegistry(captures=[record]))

    loaded = registry.load_registry()
    assert len(loaded.captures) == 1
    assert loaded.captures[0].capture_id == "rbc_bahamas_2026-08-15"
    assert loaded.captures[0].platforms_captured == ["facebook"]


def test_make_capture_id_format():
    assert make_capture_id("rbc_bahamas", CAPTURE_DATE) == "rbc_bahamas_2026-08-15"


def test_mark_capture_inserts_new_row(registry_file):
    record = mark_capture(
        BANK_ID,
        CAPTURE_DATE,
        platforms_captured=["facebook", "youtube"],
        platforms_failed=["tiktok"],
        raw_artifact_paths={
            "facebook_profile": "data/intelligence/raw/2026-08-15/rbc_bahamas/facebook.html",
        },
        scrape_status="complete",
    )

    assert record.capture_id == "rbc_bahamas_2026-08-15"
    assert record.scrape_status == "complete"
    assert record.validation_status == "pending"
    assert "tiktok" in record.platforms_failed

    loaded = registry.load_registry()
    assert len(loaded.captures) == 1


def test_mark_capture_upserts_without_duplicates(registry_file):
    mark_capture(
        BANK_ID,
        CAPTURE_DATE,
        platforms_captured=["facebook"],
        platforms_failed=[],
        raw_artifact_paths={"facebook_profile": "path/a.html"},
        scrape_status="partial",
    )
    mark_capture(
        BANK_ID,
        CAPTURE_DATE,
        platforms_captured=["facebook", "instagram"],
        platforms_failed=["tiktok"],
        raw_artifact_paths={
            "facebook_profile": "path/a.html",
            "instagram_profile": "path/b.json",
        },
        processed_path="data/intelligence/processed/2026-08-15/rbc_bahamas.json",
        scrape_status="complete",
    )

    loaded = registry.load_registry()
    assert len(loaded.captures) == 1
    row = loaded.captures[0]
    assert row.scrape_status == "complete"
    assert row.platforms_captured == ["facebook", "instagram"]
    assert row.processed_path.endswith("rbc_bahamas.json")


def test_mark_validation_updates_fields(registry_file):
    mark_capture(
        BANK_ID,
        CAPTURE_DATE,
        platforms_captured=["website"],
        platforms_failed=[],
        raw_artifact_paths={},
        scrape_status="complete",
    )

    validated_at = datetime(2026, 9, 20, 14, 0, 0, tzinfo=UTC)
    updated = mark_validation(
        "rbc_bahamas_2026-08-15",
        validation_status="validated",
        validated_at=validated_at,
        delta_variance_pct=2.5,
    )

    assert updated.validation_status == "validated"
    assert updated.validated_at == validated_at
    assert updated.delta_variance_pct == 2.5

    loaded = registry.load_registry()
    assert loaded.captures[0].validation_status == "validated"


def test_mark_capture_rejects_invalid_scrape_status(registry_file):
    with pytest.raises(ValidationError):
        mark_capture(
            BANK_ID,
            CAPTURE_DATE,
            platforms_captured=[],
            platforms_failed=[],
            raw_artifact_paths={},
            scrape_status="bogus",  # type: ignore[arg-type]
        )


def test_mark_validation_rejects_invalid_validation_status(registry_file):
    mark_capture(
        BANK_ID,
        CAPTURE_DATE,
        platforms_captured=["facebook"],
        platforms_failed=[],
        raw_artifact_paths={},
        scrape_status="complete",
    )
    with pytest.raises(ValidationError):
        mark_validation(
            "rbc_bahamas_2026-08-15",
            validation_status="bogus",  # type: ignore[arg-type]
        )


def test_mark_validation_unknown_capture_raises(registry_file):
    with pytest.raises(ValueError, match="not found"):
        mark_validation(
            "missing_bank_2026-08-15",
            validation_status="validated",
        )


def test_capture_result_raw_artifacts_map_to_registry_paths(registry_file):
    """Prove CaptureResult.raw_artifacts keys can be stored as raw_artifact_paths."""
    result = CaptureResult(
        bank_id=BANK_ID,
        capture_date=CAPTURE_DATE,
        raw_artifacts={
            "facebook_html": "data/intelligence/raw/2026-08-15/rbc/facebook.html",
        },
        errors=["twitter: unavailable"],
    )

    record = mark_capture(
        result.bank_id,
        result.capture_date,
        platforms_captured=["facebook"],
        platforms_failed=["twitter"],
        raw_artifact_paths=dict(result.raw_artifacts),
        scrape_status="partial",
    )

    assert record.raw_artifact_paths["facebook_html"].endswith(".html")
    assert "twitter" in record.platforms_failed

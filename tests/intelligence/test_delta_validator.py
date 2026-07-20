"""Tests for ingestion.intelligence.capture.delta_validator."""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from ingestion.intelligence.capture import delta_validator as dv
from ingestion.intelligence.types import (
    CaptureResult,
    Platform,
    SocialMetric,
    SourceProvenance,
    WebMetric,
)

CAPTURE_DATE = date(2026, 8, 15)


def _provenance() -> SourceProvenance:
    return SourceProvenance(
        url="https://example.com/",
        fetched_at=datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc),
        http_status=200,
        method="scrape",
    )


def _capture(
    *,
    followers: int | None = 1000,
    authority: int | None = 50,
) -> CaptureResult:
    social = []
    if followers is not None:
        social.append(
            SocialMetric(
                bank_id="commonwealth_bank",
                platform=Platform.FACEBOOK,
                capture_date=CAPTURE_DATE,
                followers=followers,
                source=_provenance(),
            )
        )
    web = [
        WebMetric(
            bank_id="commonwealth_bank",
            capture_date=CAPTURE_DATE,
            authority_score=authority,
            source=_provenance(),
        )
    ]
    return CaptureResult(
        bank_id="commonwealth_bank",
        capture_date=CAPTURE_DATE,
        social_metrics=social,
        web_metrics=web,
    )


def test_relative_variance_pct():
    assert dv.relative_variance_pct(105, 100) == pytest.approx(5.0)
    assert dv.relative_variance_pct(None, 100) is None
    assert dv.relative_variance_pct(10, 0) == 100.0
    assert dv.relative_variance_pct(0, 0) == 0.0


def test_compare_within_threshold():
    trial = dv.TrialExport(
        source="rival_iq",
        bank_id="commonwealth_bank",
        capture_date=CAPTURE_DATE,
        social=[dv.TrialSocialMetric(platform=Platform.FACEBOOK, followers=1020)],
        web=dv.TrialWebMetric(authority_score=50),
    )
    report = dv.compare_capture(_capture(followers=1000, authority=50), trial)
    assert report.validation_status == "validated"
    assert report.max_variance_pct is not None
    assert report.max_variance_pct <= 5.0
    assert not any(c.flagged for c in report.comparisons if not c.skipped)


def test_compare_flags_over_threshold():
    trial = dv.TrialExport(
        source="semrush",
        bank_id="commonwealth_bank",
        capture_date=CAPTURE_DATE,
        social=[dv.TrialSocialMetric(platform=Platform.FACEBOOK, followers=1000)],
    )
    report = dv.compare_capture(_capture(followers=1200), trial)
    assert report.validation_status == "failed"
    assert report.max_variance_pct == pytest.approx(20.0)
    flagged = [c for c in report.comparisons if c.flagged]
    assert len(flagged) == 1


def test_compare_pending_when_no_overlap():
    trial = dv.TrialExport(
        source="manual",
        bank_id="commonwealth_bank",
        capture_date=CAPTURE_DATE,
        social=[dv.TrialSocialMetric(platform=Platform.TIKTOK, followers=50)],
    )
    report = dv.compare_capture(_capture(followers=1000), trial)
    assert report.validation_status == "pending"
    assert all(c.skipped for c in report.comparisons)


def test_bank_mismatch_raises():
    trial = dv.TrialExport(
        source="rival_iq",
        bank_id="rbc_bahamas",
        capture_date=CAPTURE_DATE,
    )
    with pytest.raises(ValueError, match="bank_id mismatch"):
        dv.compare_capture(_capture(), trial)


def test_validate_capture_apply(tmp_path, monkeypatch):
    processed = tmp_path / "commonwealth_bank.json"
    processed.write_text(
        _capture(followers=1000, authority=50).model_dump_json(indent=2),
        encoding="utf-8",
    )
    trial = dv.TrialExport(
        source="rival_iq",
        bank_id="commonwealth_bank",
        capture_date=CAPTURE_DATE,
        social=[dv.TrialSocialMetric(platform=Platform.FACEBOOK, followers=1000)],
        web=dv.TrialWebMetric(authority_score=50),
    )

    marked: dict = {}

    def fake_mark(capture_id, *, validation_status, validated_at=None, delta_variance_pct=None):
        marked.update(
            {
                "capture_id": capture_id,
                "validation_status": validation_status,
                "delta_variance_pct": delta_variance_pct,
            }
        )
        return None

    monkeypatch.setattr(dv, "mark_validation", fake_mark)
    report = dv.validate_capture(trial, processed_path=processed, apply=True)
    assert report.validation_status == "validated"
    assert marked["capture_id"] == "commonwealth_bank_2026-08-15"
    assert marked["validation_status"] == "validated"

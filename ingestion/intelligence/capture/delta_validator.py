"""Compare scraped metrics against Rival IQ / SEMrush trial exports.

Trial exports are JSON files (see ``TrialExport``). Relative variance above
``VARIANCE_THRESHOLD_PCT`` (5%) flags the capture for manual review before
Issue 01 lockdown. Missing scraped or reference values are skipped — never
invented — and do not count toward the max variance.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field

from backend.app.services.document_ingestion import REPO_ROOT
from ingestion.intelligence.capture.registry import (
    make_capture_id,
    mark_validation,
    load_registry,
)
from ingestion.intelligence.types import CaptureResult, Platform

VARIANCE_THRESHOLD_PCT = 5.0

TrialSource = Literal["rival_iq", "semrush", "manual"]
ValidationOutcome = Literal["validated", "failed", "pending"]


class TrialSocialMetric(BaseModel):
    platform: Platform
    followers: Optional[int] = Field(default=None, ge=0)
    posts_in_window: Optional[int] = Field(default=None, ge=0)
    total_engagement: Optional[int] = Field(default=None, ge=0)


class TrialWebMetric(BaseModel):
    organic_traffic_est: Optional[int] = Field(default=None, ge=0)
    authority_score: Optional[int] = Field(default=None, ge=0, le=100)
    backlinks: Optional[int] = Field(default=None, ge=0)
    referring_domains: Optional[int] = Field(default=None, ge=0)
    ranking_keywords: Optional[int] = Field(default=None, ge=0)


class TrialExport(BaseModel):
    """Commercial-tool (or manual) reference snapshot for one bank/date."""

    source: TrialSource
    bank_id: str
    capture_date: date
    social: list[TrialSocialMetric] = Field(default_factory=list)
    web: Optional[TrialWebMetric] = None


class MetricDelta(BaseModel):
    field: str
    scraped: Optional[float] = None
    reference: Optional[float] = None
    variance_pct: Optional[float] = Field(default=None, ge=0)
    flagged: bool = False
    skipped: bool = False


class ValidationReport(BaseModel):
    capture_id: str
    source: TrialSource
    comparisons: list[MetricDelta] = Field(default_factory=list)
    max_variance_pct: Optional[float] = Field(default=None, ge=0)
    threshold_pct: float = VARIANCE_THRESHOLD_PCT
    validation_status: ValidationOutcome = "pending"
    notes: list[str] = Field(default_factory=list)


def relative_variance_pct(
    scraped: Optional[float],
    reference: Optional[float],
) -> Optional[float]:
    """Absolute relative variance as a percent of the reference value."""
    if scraped is None or reference is None:
        return None
    if reference == 0:
        return 0.0 if scraped == 0 else 100.0
    return abs(float(scraped) - float(reference)) / abs(float(reference)) * 100.0


def _delta(
    field: str,
    scraped: Optional[float],
    reference: Optional[float],
    *,
    threshold: float = VARIANCE_THRESHOLD_PCT,
) -> MetricDelta:
    variance = relative_variance_pct(scraped, reference)
    if variance is None:
        return MetricDelta(
            field=field,
            scraped=scraped,
            reference=reference,
            variance_pct=None,
            flagged=False,
            skipped=True,
        )
    return MetricDelta(
        field=field,
        scraped=float(scraped) if scraped is not None else None,
        reference=float(reference) if reference is not None else None,
        variance_pct=variance,
        flagged=variance > threshold,
        skipped=False,
    )


def _social_followers_by_platform(
    capture: CaptureResult,
) -> dict[Platform, Optional[int]]:
    """Prefer the first non-None followers value per platform."""
    out: dict[Platform, Optional[int]] = {}
    for metric in capture.social_metrics:
        if metric.platform not in out or out[metric.platform] is None:
            out[metric.platform] = metric.followers
    return out


def _first_web_value(
    capture: CaptureResult,
    field: str,
) -> Optional[float]:
    for metric in capture.web_metrics:
        value = getattr(metric, field, None)
        if value is not None:
            return float(value)
    return None


def compare_capture(
    capture: CaptureResult,
    trial: TrialExport,
    *,
    threshold_pct: float = VARIANCE_THRESHOLD_PCT,
) -> ValidationReport:
    """Build a field-by-field delta report for one capture vs a trial export."""
    if trial.bank_id != capture.bank_id:
        raise ValueError(
            f"bank_id mismatch: capture={capture.bank_id!r} trial={trial.bank_id!r}"
        )
    if trial.capture_date != capture.capture_date:
        raise ValueError(
            f"capture_date mismatch: capture={capture.capture_date} "
            f"trial={trial.capture_date}"
        )

    comparisons: list[MetricDelta] = []
    notes: list[str] = []
    scraped_followers = _social_followers_by_platform(capture)

    for ref in trial.social:
        comparisons.append(
            _delta(
                f"social.{ref.platform.value}.followers",
                scraped_followers.get(ref.platform),
                float(ref.followers) if ref.followers is not None else None,
                threshold=threshold_pct,
            )
        )
        if ref.posts_in_window is not None:
            scraped_posts = next(
                (
                    m.posts_in_window
                    for m in capture.social_metrics
                    if m.platform == ref.platform and m.posts_in_window is not None
                ),
                None,
            )
            comparisons.append(
                _delta(
                    f"social.{ref.platform.value}.posts_in_window",
                    float(scraped_posts) if scraped_posts is not None else None,
                    float(ref.posts_in_window),
                    threshold=threshold_pct,
                )
            )
        if ref.total_engagement is not None:
            scraped_eng = next(
                (
                    m.total_engagement
                    for m in capture.social_metrics
                    if m.platform == ref.platform and m.total_engagement is not None
                ),
                None,
            )
            comparisons.append(
                _delta(
                    f"social.{ref.platform.value}.total_engagement",
                    float(scraped_eng) if scraped_eng is not None else None,
                    float(ref.total_engagement),
                    threshold=threshold_pct,
                )
            )

    if trial.web is not None:
        for field in (
            "organic_traffic_est",
            "authority_score",
            "backlinks",
            "referring_domains",
            "ranking_keywords",
        ):
            ref_val = getattr(trial.web, field)
            if ref_val is None:
                continue
            comparisons.append(
                _delta(
                    f"web.{field}",
                    _first_web_value(capture, field),
                    float(ref_val),
                    threshold=threshold_pct,
                )
            )

    scored = [c for c in comparisons if not c.skipped and c.variance_pct is not None]
    max_variance = max((c.variance_pct for c in scored), default=None)
    flagged = [c for c in scored if c.flagged]
    skipped = [c for c in comparisons if c.skipped]

    if not scored:
        status: ValidationOutcome = "pending"
        notes.append("no overlapping numeric fields to compare")
    elif flagged:
        status = "failed"
        notes.append(
            f"{len(flagged)} field(s) exceed {threshold_pct:g}% variance threshold"
        )
    else:
        status = "validated"
        notes.append(f"all comparable fields within {threshold_pct:g}% variance")

    if skipped:
        notes.append(f"{len(skipped)} field(s) skipped (missing scraped or reference)")

    return ValidationReport(
        capture_id=make_capture_id(capture.bank_id, capture.capture_date),
        source=trial.source,
        comparisons=comparisons,
        max_variance_pct=max_variance,
        threshold_pct=threshold_pct,
        validation_status=status,
        notes=notes,
    )


def load_trial_export(path: Path) -> TrialExport:
    """Load a trial export JSON file."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    return TrialExport.model_validate(payload)


def load_processed_capture(path: Path) -> CaptureResult:
    """Load a processed capture JSON written by the orchestrator."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    return CaptureResult.model_validate(payload)


def processed_path_for(bank_id: str, capture_date: date) -> Path:
    """Resolve the canonical processed JSON path for a bank/date."""
    registry = load_registry()
    capture_id = make_capture_id(bank_id, capture_date)
    for record in registry.captures:
        if record.capture_id == capture_id and record.processed_path:
            return REPO_ROOT / record.processed_path
    return (
        REPO_ROOT
        / "data"
        / "intelligence"
        / "processed"
        / capture_date.isoformat()
        / f"{bank_id}.json"
    )


def validate_capture(
    trial: TrialExport,
    *,
    processed_path: Path | None = None,
    apply: bool = False,
    threshold_pct: float = VARIANCE_THRESHOLD_PCT,
) -> ValidationReport:
    """
    Compare a processed capture to a trial export.

    When ``apply`` is True and status is validated/failed, updates
    ``registry.json`` via ``mark_validation``.
    """
    path = processed_path or processed_path_for(trial.bank_id, trial.capture_date)
    if not path.exists():
        raise FileNotFoundError(f"Processed capture not found: {path}")

    capture = load_processed_capture(path)
    report = compare_capture(capture, trial, threshold_pct=threshold_pct)

    if apply and report.validation_status in {"validated", "failed"}:
        mark_validation(
            report.capture_id,
            validation_status=report.validation_status,
            delta_variance_pct=report.max_variance_pct,
        )

    return report

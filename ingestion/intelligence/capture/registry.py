"""Read/write data/intelligence/registry.json (architecture v0.2 §4).

Mirrors parser.load_metadata / save_metadata for the document pipeline.
Tracks each bank capture through scrape and validation state machines.

scrape_status: pending | partial | complete | failed
validation_status: pending | validated | failed
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Optional

from pydantic import AwareDatetime, BaseModel, Field

from backend.app.services.document_ingestion import INTELLIGENCE_DATA_DIR

REGISTRY_FILE = INTELLIGENCE_DATA_DIR / "registry.json"


class CaptureRecord(BaseModel):
    """One capture row in registry.json."""

    capture_id: str
    bank_id: str
    capture_date: date
    platforms_captured: list[str] = Field(default_factory=list)
    platforms_failed: list[str] = Field(default_factory=list)
    raw_artifact_paths: dict[str, str] = Field(default_factory=dict)
    processed_path: Optional[str] = None
    scrape_status: str = "pending"
    validation_status: str = "pending"
    validated_at: Optional[AwareDatetime] = None
    delta_variance_pct: Optional[float] = Field(default=None, ge=0)


class IntelligenceRegistry(BaseModel):
    """Root document for data/intelligence/registry.json."""

    captures: list[CaptureRecord] = Field(default_factory=list)


def make_capture_id(bank_id: str, capture_date: date) -> str:
    """Return the canonical capture_id for a bank and date."""
    return f"{bank_id}_{capture_date.isoformat()}"


def load_registry() -> IntelligenceRegistry:
    """Load the intelligence capture registry, or an empty default."""
    if not REGISTRY_FILE.exists():
        return IntelligenceRegistry()
    with open(REGISTRY_FILE) as file_obj:
        payload = json.load(file_obj)
    return IntelligenceRegistry.model_validate(payload)


def save_registry(registry: IntelligenceRegistry) -> None:
    """Persist the intelligence capture registry to disk."""
    INTELLIGENCE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_FILE, "w") as file_obj:
        json.dump(registry.model_dump(mode="json"), file_obj, indent=2, default=str)


def _find_capture_index(registry: IntelligenceRegistry, capture_id: str) -> int:
    for index, record in enumerate(registry.captures):
        if record.capture_id == capture_id:
            return index
    raise ValueError(f"Capture '{capture_id}' not found in registry")


def mark_capture(
    bank_id: str,
    capture_date: date,
    *,
    platforms_captured: list[str],
    platforms_failed: list[str],
    raw_artifact_paths: dict[str, str],
    processed_path: str | None = None,
    scrape_status: str = "complete",
) -> CaptureRecord:
    """Upsert a capture row after scrape (or partial scrape) completes."""
    registry = load_registry()
    capture_id = make_capture_id(bank_id, capture_date)

    record = CaptureRecord(
        capture_id=capture_id,
        bank_id=bank_id,
        capture_date=capture_date,
        platforms_captured=platforms_captured,
        platforms_failed=platforms_failed,
        raw_artifact_paths=raw_artifact_paths,
        processed_path=processed_path,
        scrape_status=scrape_status,
        validation_status="pending",
    )

    try:
        index = _find_capture_index(registry, capture_id)
        existing = registry.captures[index]
        record.validation_status = existing.validation_status
        record.validated_at = existing.validated_at
        record.delta_variance_pct = existing.delta_variance_pct
        registry.captures[index] = record
    except ValueError:
        registry.captures.append(record)

    save_registry(registry)
    return record


def mark_validation(
    capture_id: str,
    *,
    validation_status: str,
    validated_at: AwareDatetime | None = None,
    delta_variance_pct: float | None = None,
) -> CaptureRecord:
    """Update validation fields for an existing capture row."""
    registry = load_registry()
    index = _find_capture_index(registry, capture_id)
    record = registry.captures[index]

    if validated_at is None and validation_status == "validated":
        validated_at = datetime.now(timezone.utc)

    updated = record.model_copy(
        update={
            "validation_status": validation_status,
            "validated_at": validated_at,
            "delta_variance_pct": delta_variance_pct,
        }
    )
    registry.captures[index] = updated
    save_registry(registry)
    return updated

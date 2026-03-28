"""Admin ingestion orchestration endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import IngestionActor, get_ingestion_audit_logger, require_ingestion_access
from app.db.database import get_db
from app.services.ingestion_pipeline import (
    IngestionRunOptions,
    load_ingestion_status,
    run_ingestion_pipeline,
    summarize_documents,
)


router = APIRouter()


class IngestionRunRequest(BaseModel):
    """Request payload for an ingestion run."""

    run_scraper: bool = True
    run_parser: bool = True
    run_normalizer: bool = True
    run_embeddings: bool = True
    force: bool = False


class IngestionStatusResponse(BaseModel):
    """Latest orchestration status response."""

    status: str
    updated_at: str | None = None
    latest_run: dict[str, Any] | None = None
    documents: dict[str, Any]


@router.get("/status", response_model=IngestionStatusResponse)
async def get_ingestion_status(
    actor: IngestionActor = Depends(require_ingestion_access),
) -> IngestionStatusResponse:
    """Return the latest ingestion status plus current document summary."""
    status_payload = load_ingestion_status()
    return IngestionStatusResponse(
        status=status_payload.get("status", "idle"),
        updated_at=status_payload.get("updated_at"),
        latest_run=status_payload.get("latest_run"),
        documents=summarize_documents(),
    )


@router.post("/run", status_code=status.HTTP_202_ACCEPTED)
async def run_ingestion(
    payload: IngestionRunRequest,
    actor: IngestionActor = Depends(require_ingestion_access),
    audit_log=Depends(get_ingestion_audit_logger),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Run the ingestion pipeline on demand."""
    options = IngestionRunOptions(
        run_scraper=payload.run_scraper,
        run_parser=payload.run_parser,
        run_normalizer=payload.run_normalizer,
        run_embeddings=payload.run_embeddings,
        force=payload.force,
    )

    summary = await run_in_threadpool(run_ingestion_pipeline, options)

    await audit_log(
        action="run_ingestion",
        resource_type="ingestion",
        resource_id="pipeline",
        details={
            "requested_by": actor.label,
            "options": payload.model_dump(),
            "result_status": summary.get("status"),
        },
    )
    await db.commit()

    return summary

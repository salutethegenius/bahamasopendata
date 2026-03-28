"""Document serving, intake, and review API endpoints."""
from __future__ import annotations

from datetime import datetime
import math
from urllib.parse import unquote
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import (
    IngestionActor,
    get_document_audit_logger,
    get_ingestion_audit_logger,
    require_admin,
    require_document_access,
)
from app.db.database import get_db
from app.services.document_ingestion import (
    RAW_DIR,
    delete_document_storage,
    ensure_document_dirs,
    find_document_path,
    load_metadata,
    load_processed_artifact,
    register_structured_document,
    save_metadata,
    register_document_bytes,
)
from app.services.finance_publisher import (
    delete_published_document_rows,
    publish_document_to_finance_tables,
)
from app.services.ingestion_pipeline import process_single_document

router = APIRouter()


class DocumentRecord(BaseModel):
    """Document metadata returned by the API."""

    filename: str
    original_filename: str | None = None
    original_url: str | None = None
    document_type: str | None = None
    fiscal_year: str | None = None
    upload_source: str | None = None
    extraction_status: str | None = None
    file_size: int | None = None
    downloaded_at: str | None = None
    chunk_count: int | None = None
    normalization_status: str | None = None
    normalized_count: int | None = None
    embedding_status: str | None = None
    embedding_count: int | None = None
    review_status: str | None = None
    reviewed_at: str | None = None
    submitted_at: str | None = None
    publish_status: str | None = None
    published_at: str | None = None
    review_notes: str | None = None
    exists_on_disk: bool


class UploadDocumentResponse(BaseModel):
    """Response payload for document uploads."""

    document: DocumentRecord
    duplicate: bool
    processing: dict[str, Any] | None = None


class DeleteDocumentResponse(BaseModel):
    """Response payload for document deletion."""

    filename: str
    deleted: bool
    storage: dict[str, int]
    published_rows: dict[str, int]


class StructuredDataPayload(BaseModel):
    """Formatted structured data that can be uploaded directly."""

    model_config = ConfigDict(extra="allow")

    source_document: str | None = None
    title: str | None = None
    document_type: str
    fiscal_year: str | None = None
    executive_summary: str = ""
    ministries: list[str] = []
    extracted_items: list[dict[str, Any]] = []
    notable_topics: list[str] = []
    warnings: list[str] = []
    confidence: float = 1.0
    needs_review: bool = False


class StructuredUploadRequest(BaseModel):
    """Request body for direct structured-data upload."""

    title: str | None = None
    document_type: str
    fiscal_year: str | None = None
    source_url: str | None = None
    structured_data: StructuredDataPayload
    review_notes: str | None = None
    submit_after_upload: bool = False


class ProcessDocumentRequest(BaseModel):
    """Controls for processing one document."""

    run_parser: bool = True
    run_normalizer: bool | None = False
    enable_ai_scan: bool | None = None
    run_embeddings: bool | None = False
    enable_search_indexing: bool | None = None
    force: bool = False

    def resolved_run_normalizer(self) -> bool:
        """Resolve the AI normalization flag."""
        if self.enable_ai_scan is not None:
            return self.enable_ai_scan
        return bool(self.run_normalizer)

    def resolved_run_embeddings(self) -> bool:
        """Resolve the embedding/search flag."""
        if self.enable_search_indexing is not None:
            return self.enable_search_indexing
        return bool(self.run_embeddings)


class SubmitDocumentRequest(BaseModel):
    """Optional notes for human review submission."""

    review_notes: str | None = None


class ReviewPagePreview(BaseModel):
    """Short text sample from extracted page output."""

    page_number: int
    text: str
    char_count: int | None = None


class ReviewTablePreview(BaseModel):
    """Short table sample from extracted table output."""

    page_number: int | None = None
    columns: list[str] = []
    rows: list[list[Any]] = []


class ExtractionReview(BaseModel):
    """Structured extraction review details."""

    available: bool
    status: str
    page_count: int = 0
    table_count: int = 0
    chunk_count: int = 0
    sample_pages: list[ReviewPagePreview] = []
    sample_tables: list[ReviewTablePreview] = []


class AIReview(BaseModel):
    """AI processing review details."""

    available: bool
    status: str
    model: str | None = None
    confidence: float | None = None
    needs_review: bool | None = None
    executive_summary: str | None = None
    ministries: list[str] = []
    notable_topics: list[str] = []
    warnings: list[str] = []
    extracted_item_count: int = 0
    preview_json: dict[str, Any] | None = None


class SubmissionReview(BaseModel):
    """Final review and submission state for a document."""

    can_submit: bool
    can_publish: bool
    can_unapprove: bool
    review_status: str
    reviewed_at: str | None = None
    submitted_at: str | None = None
    publish_status: str | None = None
    published_at: str | None = None
    review_notes: str | None = None


class DocumentReviewResponse(BaseModel):
    """Review payload used by the admin section UI."""

    document: DocumentRecord
    extraction: ExtractionReview
    ai_processing: AIReview
    submission: SubmissionReview


class PublishDocumentResponse(BaseModel):
    """Response payload for explicit publish actions."""

    filename: str
    publish_status: str
    published_at: str | None = None
    published_records: dict[str, int]
    warnings: list[str] = []


def _serialize_document_record(doc: dict) -> DocumentRecord:
    """Convert metadata JSON record to a response model."""
    extraction_status = doc.get("extraction_status") or "waiting_for_processing"
    normalization_status = doc.get("normalization_status") or (
        "pending" if extraction_status == "success" else "waiting_for_processing"
    )
    embedding_status = doc.get("embedding_status") or (
        "pending" if extraction_status == "success" else "waiting_for_processing"
    )

    return DocumentRecord(
        filename=doc["filename"],
        original_filename=doc.get("original_filename"),
        original_url=doc.get("original_url"),
        document_type=doc.get("document_type"),
        fiscal_year=doc.get("fiscal_year"),
        upload_source=doc.get("upload_source"),
        extraction_status=extraction_status,
        file_size=doc.get("file_size"),
        downloaded_at=doc.get("downloaded_at"),
        chunk_count=doc.get("chunk_count"),
        normalization_status=normalization_status,
        normalized_count=doc.get("normalized_count"),
        embedding_status=embedding_status,
        embedding_count=doc.get("embedding_count"),
        review_status=_resolve_review_status(doc),
        reviewed_at=doc.get("reviewed_at"),
        submitted_at=doc.get("submitted_at"),
        publish_status=doc.get("publish_status"),
        published_at=doc.get("published_at"),
        review_notes=doc.get("review_notes"),
        exists_on_disk=(RAW_DIR / doc["filename"]).exists(),
    )


def _resolve_review_status(doc: dict[str, Any]) -> str:
    """Derive the current review status from document metadata."""
    explicit = doc.get("review_status")
    if explicit:
        return explicit
    if doc.get("submitted_at"):
        return "approved"
    if doc.get("extraction_status") == "success":
        return "pending_review"
    return "waiting_for_processing"


def _find_document_or_404(filename: str) -> dict[str, Any]:
    """Load one metadata document or raise 404."""
    metadata = load_metadata()
    for doc in metadata.get("documents", []):
        if doc.get("filename") == filename:
            return doc
    raise HTTPException(status_code=404, detail=f"Document '{filename}' not found in metadata")


def _coerce_preview_value(value: Any) -> Any:
    """Normalize preview values so review payloads stay JSON-safe."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return ""
    return value


def _build_table_preview(table: dict[str, Any]) -> ReviewTablePreview:
    """Convert parser table output into a stable review preview shape."""
    raw_columns = table.get("columns") or []
    columns = [
        str(_coerce_preview_value(column)).strip()
        for column in raw_columns
        if str(_coerce_preview_value(column)).strip()
    ]

    raw_rows = table.get("data") or []
    rows: list[list[Any]] = []
    for row in raw_rows[:5]:
        if isinstance(row, list):
            rows.append([_coerce_preview_value(cell) for cell in row])
            continue
        if isinstance(row, dict):
            if columns:
                rows.append([_coerce_preview_value(row.get(column)) for column in columns])
            else:
                rows.append([_coerce_preview_value(value) for value in row.values()])

    return ReviewTablePreview(
        page_number=table.get("page_number"),
        columns=columns,
        rows=rows,
    )


def _build_review_response(doc: dict[str, Any]) -> DocumentReviewResponse:
    """Assemble a review response from metadata plus processed artifacts."""
    text_payload = load_processed_artifact(doc["filename"], "text") or {}
    tables_payload = load_processed_artifact(doc["filename"], "tables") or {}
    normalized_payload = load_processed_artifact(doc["filename"], "normalized") or {}

    pages = text_payload.get("pages", [])
    tables = tables_payload.get("tables", [])
    extraction_available = bool(text_payload or tables_payload)

    sample_pages = [
        ReviewPagePreview(
            page_number=page.get("page_number", 0),
            text=" ".join((page.get("text") or "").split())[:600],
            char_count=page.get("char_count"),
        )
        for page in pages[:3]
        if page.get("page_number")
    ]

    sample_tables = [_build_table_preview(table) for table in tables[:2]]

    ai_available = bool(normalized_payload)
    preview_json = None
    if ai_available:
        preview_json = {
            "document_type": normalized_payload.get("document_type"),
            "fiscal_year": normalized_payload.get("fiscal_year"),
            "executive_summary": normalized_payload.get("executive_summary"),
            "ministries": normalized_payload.get("ministries", [])[:8],
            "extracted_items": normalized_payload.get("extracted_items", [])[:5],
            "warnings": normalized_payload.get("warnings", []),
            "confidence": normalized_payload.get("confidence"),
            "needs_review": normalized_payload.get("needs_review"),
        }

    review_status = _resolve_review_status(doc)
    can_submit = doc.get("extraction_status") == "success"
    can_publish = review_status == "approved"

    return DocumentReviewResponse(
        document=_serialize_document_record(doc),
        extraction=ExtractionReview(
            available=extraction_available,
            status=doc.get("extraction_status") or "pending",
            page_count=len(pages),
            table_count=len(tables),
            chunk_count=doc.get("chunk_count") or 0,
            sample_pages=sample_pages,
            sample_tables=sample_tables,
        ),
        ai_processing=AIReview(
            available=ai_available,
            status=doc.get("normalization_status") or "pending",
            model=normalized_payload.get("normalization_model") or doc.get("normalization_model"),
            confidence=normalized_payload.get("confidence"),
            needs_review=normalized_payload.get("needs_review"),
            executive_summary=normalized_payload.get("executive_summary"),
            ministries=normalized_payload.get("ministries", []),
            notable_topics=normalized_payload.get("notable_topics", []),
            warnings=normalized_payload.get("warnings", []),
            extracted_item_count=len(normalized_payload.get("extracted_items", [])),
            preview_json=preview_json,
        ),
        submission=SubmissionReview(
            can_submit=can_submit,
            can_publish=can_publish,
            can_unapprove=review_status == "approved" and doc.get("publish_status") != "success",
            review_status=review_status,
            reviewed_at=doc.get("reviewed_at"),
            submitted_at=doc.get("submitted_at"),
            publish_status=doc.get("publish_status"),
            published_at=doc.get("published_at"),
            review_notes=doc.get("review_notes"),
        ),
    )


@router.post("/upload", response_model=UploadDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str | None = Form(default=None),
    fiscal_year: str | None = Form(default=None),
    source_url: str | None = Form(default=None),
    auto_process: bool = Form(default=False),
    enable_ai_scan: bool = Form(default=False),
    enable_search_indexing: bool = Form(default=False),
    force_process: bool = Form(default=False),
    actor: IngestionActor = Depends(require_document_access),
    audit_log=Depends(get_document_audit_logger),
    db: AsyncSession = Depends(get_db),
):
    """Upload a source PDF into canonical storage and register metadata."""
    ensure_document_dirs()

    filename = file.filename or ""
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    doc_meta, created = register_document_bytes(
        content=content,
        original_filename=filename,
        original_url=source_url,
        document_type=document_type,
        fiscal_year=fiscal_year,
        upload_source="api",
    )

    should_process = auto_process or enable_ai_scan or enable_search_indexing
    processing_result: dict[str, Any] | None = None
    if should_process:
        processing_result = await run_in_threadpool(
            process_single_document,
            doc_meta["filename"],
            run_parser=True,
            run_normalizer=enable_ai_scan,
            run_embeddings=enable_search_indexing,
            force=force_process,
        )

        metadata = load_metadata()
        for doc in metadata.get("documents", []):
            if doc.get("filename") != doc_meta["filename"]:
                continue
            doc["review_status"] = "pending_review"
            doc["publish_status"] = "pending"
            doc.pop("published_at", None)
            doc.pop("reviewed_at", None)
            doc.pop("submitted_at", None)
            doc.pop("review_notes", None)
            doc_meta = doc
            save_metadata(metadata)
            break

    await audit_log(
        action="upload" if created else "upload_duplicate",
        resource_type="document",
        resource_id=doc_meta["filename"],
        details={
            "original_filename": filename,
            "document_type": doc_meta.get("document_type"),
            "fiscal_year": doc_meta.get("fiscal_year"),
            "duplicate": not created,
            "uploaded_by": actor.label,
            "auto_process": should_process,
            "enable_ai_scan": enable_ai_scan,
            "enable_search_indexing": enable_search_indexing,
        },
    )
    await db.commit()

    return UploadDocumentResponse(
        document=_serialize_document_record(doc_meta),
        duplicate=not created,
        processing=processing_result,
    )


@router.post("/upload-structured", response_model=UploadDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_structured_document(
    payload: StructuredUploadRequest,
    actor: IngestionActor = Depends(require_document_access),
    audit_log=Depends(get_document_audit_logger),
    db: AsyncSession = Depends(get_db),
):
    """Upload already-formatted structured data directly into review."""
    doc_meta, created = register_structured_document(
        title=payload.title,
        document_type=payload.document_type,
        structured_data=payload.structured_data.model_dump(),
        original_url=payload.source_url,
        fiscal_year=payload.fiscal_year,
        upload_source="structured_api",
        submit_after_upload=payload.submit_after_upload,
        review_notes=payload.review_notes,
    )

    if payload.submit_after_upload:
        reviewed_at = datetime.now().isoformat()
        doc_meta["review_status"] = "approved"
        doc_meta["reviewed_at"] = reviewed_at
        doc_meta["submitted_at"] = reviewed_at
        doc_meta["publish_status"] = "pending"
        metadata = load_metadata()
        for existing_doc in metadata.get("documents", []):
            if existing_doc.get("filename") == doc_meta["filename"]:
                existing_doc.update(doc_meta)
                break
        save_metadata(metadata)

    await audit_log(
        action="upload_structured" if created else "upload_structured_duplicate",
        resource_type="document",
        resource_id=doc_meta["filename"],
        details={
            "document_type": doc_meta.get("document_type"),
            "fiscal_year": doc_meta.get("fiscal_year"),
            "duplicate": not created,
            "uploaded_by": actor.label,
            "submit_after_upload": payload.submit_after_upload,
            "review_status": doc_meta.get("review_status"),
        },
    )
    await db.commit()

    return UploadDocumentResponse(
        document=_serialize_document_record(doc_meta),
        duplicate=not created,
        processing=None,
    )


@router.post("/{filename}/process")
async def process_document_endpoint(
    filename: str,
    payload: ProcessDocumentRequest,
    actor: IngestionActor = Depends(require_document_access),
    audit_log=Depends(get_document_audit_logger),
    db: AsyncSession = Depends(get_db),
):
    """Process one document through parser, normalizer, and embeddings."""
    filename = unquote(filename)
    metadata = load_metadata()
    if not any(doc.get("filename") == filename for doc in metadata.get("documents", [])):
        raise HTTPException(status_code=404, detail=f"Document '{filename}' not found in metadata")

    result = await run_in_threadpool(
        process_single_document,
        filename,
        run_parser=payload.run_parser,
        run_normalizer=payload.resolved_run_normalizer(),
        run_embeddings=payload.resolved_run_embeddings(),
        force=payload.force,
    )

    await audit_log(
        action="process_document",
        resource_type="document",
        resource_id=filename,
        details={
            "requested_by": actor.label,
            "options": payload.model_dump(),
            "result_status": result.get("status"),
        },
    )
    metadata = load_metadata()
    for doc in metadata.get("documents", []):
        if doc.get("filename") != filename:
            continue
        doc["review_status"] = "pending_review"
        doc["publish_status"] = "pending"
        doc.pop("published_at", None)
        doc.pop("reviewed_at", None)
        doc.pop("submitted_at", None)
        doc.pop("review_notes", None)
        save_metadata(metadata)
        break
    await db.commit()
    return result


@router.get("/{filename}/review", response_model=DocumentReviewResponse)
async def get_document_review(
    filename: str,
    actor: IngestionActor = Depends(require_document_access),
):
    """Return extraction, AI organization, and review-ready data for one document."""
    del actor
    filename = unquote(filename)
    doc = _find_document_or_404(filename)
    return _build_review_response(doc)


@router.post("/{filename}/submit", response_model=DocumentReviewResponse)
async def submit_document_review(
    filename: str,
    payload: SubmitDocumentRequest,
    actor: IngestionActor = Depends(require_document_access),
    audit_log=Depends(get_document_audit_logger),
    db: AsyncSession = Depends(get_db),
):
    """Mark a reviewed document as approved and ready to publish."""
    filename = unquote(filename)
    metadata = load_metadata()
    target_doc = next((doc for doc in metadata.get("documents", []) if doc.get("filename") == filename), None)
    if target_doc is None:
        raise HTTPException(status_code=404, detail=f"Document '{filename}' not found in metadata")
    if target_doc.get("extraction_status") != "success":
        raise HTTPException(status_code=409, detail="Document must be extracted successfully before submission")

    reviewed_at = datetime.now().isoformat()
    target_doc["review_status"] = "approved"
    target_doc["reviewed_at"] = reviewed_at
    target_doc["submitted_at"] = reviewed_at
    target_doc["review_notes"] = payload.review_notes
    target_doc["publish_status"] = "pending"
    target_doc.pop("published_at", None)
    target_doc.pop("publish_result", None)
    save_metadata(metadata)

    await audit_log(
        action="submit_document_review",
        resource_type="document",
        resource_id=filename,
        details={
            "submitted_by": actor.label,
            "review_notes": payload.review_notes,
            "publish_status": target_doc.get("publish_status"),
        },
    )
    await db.commit()
    return _build_review_response(target_doc)


@router.post("/{filename}/unapprove", response_model=DocumentReviewResponse)
async def unapprove_document_review(
    filename: str,
    actor: IngestionActor = Depends(require_document_access),
    audit_log=Depends(get_document_audit_logger),
    db: AsyncSession = Depends(get_db),
):
    """Move an approved document back to pending review."""
    filename = unquote(filename)
    metadata = load_metadata()
    target_doc = next((doc for doc in metadata.get("documents", []) if doc.get("filename") == filename), None)
    if target_doc is None:
        raise HTTPException(status_code=404, detail=f"Document '{filename}' not found in metadata")

    review_status = _resolve_review_status(target_doc)
    if review_status != "approved":
        raise HTTPException(status_code=409, detail="Only approved documents can be unapproved")

    if target_doc.get("publish_status") == "success":
        raise HTTPException(
            status_code=409,
            detail="Published documents cannot be unapproved. Remove them from the live dataset first.",
        )

    target_doc["review_status"] = "pending_review"
    target_doc.pop("reviewed_at", None)
    target_doc.pop("submitted_at", None)
    target_doc["publish_status"] = "pending"
    target_doc.pop("published_at", None)
    target_doc.pop("publish_result", None)
    save_metadata(metadata)

    await audit_log(
        action="unapprove_document_review",
        resource_type="document",
        resource_id=filename,
        details={
            "unapproved_by": actor.label,
            "review_status": target_doc.get("review_status"),
            "publish_status": target_doc.get("publish_status"),
        },
    )
    await db.commit()
    return _build_review_response(target_doc)


@router.post("/{filename}/publish", response_model=PublishDocumentResponse)
async def publish_document_review(
    filename: str,
    actor: IngestionActor = Depends(require_document_access),
    audit_log=Depends(get_document_audit_logger),
    db: AsyncSession = Depends(get_db),
):
    """Publish an approved document into the live finance tables."""
    filename = unquote(filename)
    metadata = load_metadata()
    target_doc = next((doc for doc in metadata.get("documents", []) if doc.get("filename") == filename), None)
    if target_doc is None:
        raise HTTPException(status_code=404, detail=f"Document '{filename}' not found in metadata")
    if _resolve_review_status(target_doc) != "approved":
        raise HTTPException(status_code=409, detail="Document must be approved before it can be published")
    if target_doc.get("extraction_status") != "success":
        raise HTTPException(status_code=409, detail="Document must be extracted successfully before publishing")

    published_at = datetime.now().isoformat()
    publish_result = await publish_document_to_finance_tables(db, doc_meta=target_doc)
    target_doc["publish_status"] = publish_result.status
    target_doc["published_at"] = published_at
    target_doc["publish_result"] = publish_result.as_dict()
    save_metadata(metadata)

    await audit_log(
        action="publish_document",
        resource_type="document",
        resource_id=filename,
        details={
            "published_by": actor.label,
            "publish_status": publish_result.status,
            "published_records": publish_result.published_records,
            "publish_warnings": publish_result.warnings,
        },
    )
    await db.commit()

    return PublishDocumentResponse(
        filename=filename,
        publish_status=publish_result.status,
        published_at=published_at,
        published_records=publish_result.published_records,
        warnings=publish_result.warnings,
    )


@router.delete("/{filename}", response_model=DeleteDocumentResponse)
async def delete_document(
    filename: str,
    current_user=Depends(require_admin),
    audit_log=Depends(get_ingestion_audit_logger),
    db: AsyncSession = Depends(get_db),
):
    """Delete a stored document, its artifacts, and any published finance rows."""
    actor = IngestionActor(user=current_user)
    filename = unquote(filename)
    _find_document_or_404(filename)

    published_rows = await delete_published_document_rows(db, filename)
    storage_result = await run_in_threadpool(delete_document_storage, filename)

    await audit_log(
        action="delete_document",
        resource_type="document",
        resource_id=filename,
        details={
            "deleted_by": actor.label,
            "storage": storage_result,
            "published_rows": published_rows,
        },
    )
    await db.commit()

    return DeleteDocumentResponse(
        filename=filename,
        deleted=True,
        storage=storage_result,
        published_rows=published_rows,
    )


@router.get("/{filename}")
async def get_document(
    filename: str,
    page: int = Query(None, description="Page number to jump to in PDF viewer")
):
    """
    Serve a PDF document.
    
    If page is provided, returns a response that can be used to open the PDF
    at a specific page (browser-dependent).
    """
    filename = unquote(filename)

    file_path = find_document_path(filename)
    if not file_path or not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Document '{filename}' not found. Available: {[f.name for f in RAW_DIR.glob('*.pdf')]}"
        )

    # Return PDF file
    if page:
        return FileResponse(
            file_path,
            media_type="application/pdf",
            filename=filename,
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
            }
        )
    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=filename,
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
        }
    )


@router.get("", response_model=dict[str, list[DocumentRecord]])
async def list_documents(
    actor: IngestionActor = Depends(require_document_access),
):
    """List known documents from metadata plus any orphan PDFs in raw storage."""
    del actor
    ensure_document_dirs()
    metadata = load_metadata()
    documents: list[DocumentRecord] = []
    seen: set[str] = set()

    for doc in metadata.get("documents", []):
        documents.append(_serialize_document_record(doc))
        seen.add(doc["filename"])

    for file_path in RAW_DIR.glob("*.pdf"):
        if file_path.name in seen:
            continue
        documents.append(
            DocumentRecord(
                filename=file_path.name,
                original_filename=None,
                original_url=None,
                document_type=None,
                fiscal_year=None,
                upload_source="filesystem",
                extraction_status=None,
                file_size=file_path.stat().st_size,
                downloaded_at=None,
                chunk_count=None,
                normalization_status=None,
                normalized_count=None,
                embedding_status=None,
                embedding_count=None,
                exists_on_disk=True,
            )
        )

    documents.sort(key=lambda doc: doc.downloaded_at or "", reverse=True)
    return {"documents": documents}

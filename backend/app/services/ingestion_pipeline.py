"""Shared ingestion orchestration for scripts and API endpoints."""
from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .document_ingestion import DATA_DIR, REPO_ROOT, ensure_document_dirs


STATUS_FILE = DATA_DIR / "ingestion_status.json"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ingestion import ai_normalizer, embeddings, parser, scraper  # noqa: E402


@dataclass
class IngestionRunOptions:
    """Options for a single ingestion pipeline run."""

    run_scraper: bool = True
    run_parser: bool = True
    run_normalizer: bool = True
    run_embeddings: bool = True
    force: bool = False


def _now() -> str:
    return datetime.now().isoformat()


def load_ingestion_status() -> dict[str, Any]:
    """Load the latest ingestion status file."""
    if STATUS_FILE.exists():
        with open(STATUS_FILE) as file_obj:
            return json.load(file_obj)
    return {
        "status": "idle",
        "updated_at": None,
        "latest_run": None,
    }


def save_ingestion_status(status_payload: dict[str, Any]) -> None:
    """Persist the latest ingestion status file."""
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATUS_FILE, "w") as file_obj:
        json.dump(status_payload, file_obj, indent=2, default=str)


def summarize_documents() -> dict[str, Any]:
    """Summarize current document processing state from metadata."""
    metadata = parser.load_metadata()
    documents = metadata.get("documents", [])
    return {
        "document_count": len(documents),
        "extraction_pending": sum(1 for doc in documents if doc.get("extraction_status") == "pending"),
        "extraction_success": sum(1 for doc in documents if doc.get("extraction_status") == "success"),
        "embedding_success": sum(1 for doc in documents if doc.get("embedding_status") == "success"),
        "normalization_success": sum(1 for doc in documents if doc.get("normalization_status") == "success"),
    }


def _run_scraper_stage(force: bool) -> dict[str, Any]:
    """Run the scraper stage."""
    before_summary = summarize_documents()
    pdf_links = scraper.asyncio.run(scraper.scrape_budget_site())
    if not pdf_links:
        pdf_links = [{"url": doc["url"], "name": doc["name"]} for doc in scraper.KNOWN_DOCUMENTS]
    scraper.asyncio.run(scraper.download_documents(pdf_links))
    after_summary = summarize_documents()
    return {
        "status": "success",
        "discovered_links": len(pdf_links),
        "documents_before": before_summary["document_count"],
        "documents_after": after_summary["document_count"],
        "force": force,
    }


def _run_parser_stage(force: bool) -> dict[str, Any]:
    """Run the parser stage against pending or forced documents."""
    ensure_document_dirs()
    parser.ensure_dirs()
    metadata = parser.load_metadata()
    processed = 0
    skipped = 0

    for doc in metadata.get("documents", []):
        if not force and doc.get("extraction_status") == "success":
            skipped += 1
            continue

        result = parser.process_document(doc)
        doc["extraction_status"] = result["status"]
        doc["extraction_result"] = result
        doc["extracted_at"] = _now()

        if result["status"] == "success":
            chunks = parser.create_document_chunks(doc)
            doc["chunk_count"] = len(chunks)
        else:
            doc["chunk_count"] = doc.get("chunk_count", 0)

        processed += 1
        parser.save_metadata(metadata)

    return {
        "status": "success",
        "processed_documents": processed,
        "skipped_documents": skipped,
    }


def _run_normalizer_stage(force: bool) -> dict[str, Any]:
    """Run the Gemini normalization stage."""
    metadata = ai_normalizer.load_metadata()
    if not ai_normalizer.get_gemini_api_key():
        return {
            "status": "skipped",
            "reason": "GEMINI_API_KEY not configured",
        }

    processed = 0
    skipped = 0
    failed = 0

    for doc in metadata.get("documents", []):
        if doc.get("extraction_status") != "success":
            skipped += 1
            continue
        if not force and doc.get("normalization_status") == "success":
            skipped += 1
            continue

        try:
            result = ai_normalizer.normalize_document(doc)
        except ai_normalizer.ValidationError as exc:
            failed += 1
            result = {
                "status": "validation_error",
                "normalized_count": 0,
                "error": exc.errors(),
            }
        except Exception as exc:
            failed += 1
            result = {
                "status": "error",
                "normalized_count": 0,
                "error": str(exc),
            }

        doc["normalization_status"] = result["status"]
        doc["normalization_result"] = result
        doc["normalization_provider"] = "gemini"
        doc["normalization_model"] = ai_normalizer.get_gemini_model()
        doc["normalized_at"] = _now()
        doc["normalized_count"] = result.get("normalized_count", 0)
        processed += 1
        ai_normalizer.save_metadata(metadata)

    return {
        "status": "success" if failed == 0 else "partial_success",
        "processed_documents": processed,
        "skipped_documents": skipped,
        "failed_documents": failed,
    }


def _run_embeddings_stage(force: bool) -> dict[str, Any]:
    """Run the embeddings stage."""
    embeddings.ensure_dirs()
    try:
        openai_client = embeddings.get_openai_client()
        pinecone_client = embeddings.get_pinecone_client()
        pinecone_index = embeddings.init_pinecone_index(pinecone_client)
    except ValueError as exc:
        return {
            "status": "skipped",
            "reason": str(exc),
        }

    metadata = embeddings.load_metadata()
    processed = 0
    skipped = 0
    failed = 0

    for doc in metadata.get("documents", []):
        if doc.get("extraction_status") != "success":
            skipped += 1
            continue
        if not force and doc.get("embedding_status") == "success":
            skipped += 1
            continue

        try:
            result = embeddings.process_document_embeddings(doc, openai_client, pinecone_index)
        except Exception as exc:
            failed += 1
            result = {
                "status": "error",
                "embedded": 0,
                "error": str(exc),
            }

        doc["embedding_status"] = result["status"]
        doc["embedding_count"] = result.get("embedded", 0)
        doc["embedded_at"] = _now()
        processed += 1
        embeddings.save_metadata(metadata)

    return {
        "status": "success" if failed == 0 else "partial_success",
        "processed_documents": processed,
        "skipped_documents": skipped,
        "failed_documents": failed,
    }


def process_single_document(
    filename: str,
    *,
    run_parser: bool = True,
    run_normalizer: bool = True,
    run_embeddings: bool = True,
    force: bool = False,
) -> dict[str, Any]:
    """Process one document through parser, normalizer, and embeddings."""
    ensure_document_dirs()
    metadata = parser.load_metadata()
    target_doc = next((doc for doc in metadata.get("documents", []) if doc.get("filename") == filename), None)
    if target_doc is None:
        raise FileNotFoundError(f"Document '{filename}' is not registered in metadata")

    summary: dict[str, Any] = {
        "filename": filename,
        "status": "success",
        "stages": {},
    }

    if run_parser:
        if force or target_doc.get("extraction_status") != "success":
            parser_result = parser.process_document(target_doc)
            target_doc["extraction_status"] = parser_result["status"]
            target_doc["extraction_result"] = parser_result
            target_doc["extracted_at"] = _now()
            if parser_result["status"] == "success":
                chunks = parser.create_document_chunks(target_doc)
                target_doc["chunk_count"] = len(chunks)
            parser.save_metadata(metadata)
        else:
            parser_result = {"status": "skipped", "reason": "already_extracted"}
        summary["stages"]["parser"] = parser_result
    else:
        summary["stages"]["parser"] = {"status": "skipped"}

    if run_normalizer:
        metadata = ai_normalizer.load_metadata()
        target_doc = next((doc for doc in metadata.get("documents", []) if doc.get("filename") == filename), None)
        if not ai_normalizer.get_gemini_api_key():
            normalizer_result = {"status": "skipped", "reason": "GEMINI_API_KEY not configured"}
        elif target_doc and target_doc.get("extraction_status") == "success":
            if force or target_doc.get("normalization_status") != "success":
                try:
                    normalizer_result = ai_normalizer.normalize_document(target_doc)
                except ai_normalizer.ValidationError as exc:
                    normalizer_result = {
                        "status": "validation_error",
                        "normalized_count": 0,
                        "error": exc.errors(),
                    }
                except Exception as exc:
                    normalizer_result = {
                        "status": "error",
                        "normalized_count": 0,
                        "error": str(exc),
                    }
                target_doc["normalization_status"] = normalizer_result["status"]
                target_doc["normalization_result"] = normalizer_result
                target_doc["normalization_provider"] = "gemini"
                target_doc["normalization_model"] = ai_normalizer.get_gemini_model()
                target_doc["normalized_at"] = _now()
                target_doc["normalized_count"] = normalizer_result.get("normalized_count", 0)
                ai_normalizer.save_metadata(metadata)
            else:
                normalizer_result = {"status": "skipped", "reason": "already_normalized"}
        else:
            normalizer_result = {"status": "skipped", "reason": "not_extracted"}
        summary["stages"]["normalizer"] = normalizer_result
    else:
        summary["stages"]["normalizer"] = {"status": "skipped"}

    if run_embeddings:
        metadata = embeddings.load_metadata()
        target_doc = next((doc for doc in metadata.get("documents", []) if doc.get("filename") == filename), None)
        try:
            openai_client = embeddings.get_openai_client()
            pinecone_client = embeddings.get_pinecone_client()
            pinecone_index = embeddings.init_pinecone_index(pinecone_client)
        except ValueError as exc:
            embedding_result = {"status": "skipped", "reason": str(exc)}
        else:
            if target_doc and target_doc.get("extraction_status") == "success":
                if force or target_doc.get("embedding_status") != "success":
                    try:
                        embedding_result = embeddings.process_document_embeddings(
                            target_doc,
                            openai_client,
                            pinecone_index,
                        )
                    except Exception as exc:
                        embedding_result = {
                            "status": "error",
                            "embedded": 0,
                            "error": str(exc),
                        }
                    target_doc["embedding_status"] = embedding_result["status"]
                    target_doc["embedding_count"] = embedding_result.get("embedded", 0)
                    target_doc["embedded_at"] = _now()
                    embeddings.save_metadata(metadata)
                else:
                    embedding_result = {"status": "skipped", "reason": "already_embedded"}
            else:
                embedding_result = {"status": "skipped", "reason": "not_extracted"}
        summary["stages"]["embeddings"] = embedding_result
    else:
        summary["stages"]["embeddings"] = {"status": "skipped"}

    stage_statuses = [result.get("status") for result in summary["stages"].values()]
    if any(status == "error" for status in stage_statuses):
        summary["status"] = "error"
    elif any(status == "validation_error" for status in stage_statuses):
        summary["status"] = "partial_success"
    else:
        summary["status"] = "success"

    return summary


def run_ingestion_pipeline(options: IngestionRunOptions | None = None) -> dict[str, Any]:
    """Run the end-to-end ingestion pipeline and persist status."""
    options = options or IngestionRunOptions()
    start_time = _now()

    run_summary: dict[str, Any] = {
        "status": "running",
        "started_at": start_time,
        "completed_at": None,
        "options": asdict(options),
        "stages": {},
        "documents": summarize_documents(),
    }
    save_ingestion_status(
        {
            "status": "running",
            "updated_at": start_time,
            "latest_run": run_summary,
        }
    )

    stage_errors: list[str] = []

    try:
        if options.run_scraper:
            run_summary["stages"]["scraper"] = _run_scraper_stage(options.force)
        else:
            run_summary["stages"]["scraper"] = {"status": "skipped"}

        if options.run_parser:
            run_summary["stages"]["parser"] = _run_parser_stage(options.force)
        else:
            run_summary["stages"]["parser"] = {"status": "skipped"}

        if options.run_normalizer:
            run_summary["stages"]["normalizer"] = _run_normalizer_stage(options.force)
        else:
            run_summary["stages"]["normalizer"] = {"status": "skipped"}

        if options.run_embeddings:
            run_summary["stages"]["embeddings"] = _run_embeddings_stage(options.force)
        else:
            run_summary["stages"]["embeddings"] = {"status": "skipped"}

        for stage_name, stage_result in run_summary["stages"].items():
            if stage_result.get("status") in {"error", "partial_success"}:
                stage_errors.append(stage_name)

        run_summary["status"] = "success" if not stage_errors else "partial_success"
    except Exception as exc:
        run_summary["status"] = "error"
        run_summary["error"] = str(exc)
    finally:
        run_summary["completed_at"] = _now()
        run_summary["documents"] = summarize_documents()
        save_ingestion_status(
            {
                "status": run_summary["status"],
                "updated_at": run_summary["completed_at"],
                "latest_run": run_summary,
            }
        )

    return run_summary

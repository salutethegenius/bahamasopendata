"""Shared helpers for document intake, storage, and metadata registration."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional


REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
EMBEDDINGS_DIR = DATA_DIR / "embeddings"
METADATA_FILE = DATA_DIR / "document_metadata.json"


def ensure_document_dirs() -> None:
    """Create document storage directories if they do not already exist."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    normalize_legacy_uploads()


def compute_sha256_bytes(content: bytes) -> str:
    """Compute SHA-256 for in-memory content."""
    return hashlib.sha256(content).hexdigest()


def compute_file_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of a file on disk."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_metadata() -> dict:
    """Load metadata JSON or return an empty default structure."""
    if METADATA_FILE.exists():
        with open(METADATA_FILE) as file_obj:
            return json.load(file_obj)
    return {"documents": []}


def save_metadata(metadata: dict) -> None:
    """Persist metadata JSON to disk."""
    METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(METADATA_FILE, "w") as file_obj:
        json.dump(metadata, file_obj, indent=2, default=str)


def sanitize_filename(filename: str) -> str:
    """Normalize an incoming filename into the project's safe PDF naming style."""
    safe_name = "".join(
        char if char.isalnum() or char in "._- " else "_"
        for char in filename
    ).strip()
    if not safe_name.lower().endswith(".pdf"):
        safe_name += ".pdf"
    return safe_name or "document.pdf"


def sanitize_storage_name(filename: str, *, default_name: str, extension: str) -> str:
    """Normalize a storage filename without forcing PDF semantics."""
    safe_name = "".join(
        char if char.isalnum() or char in "._- " else "_"
        for char in filename
    ).strip()
    if not safe_name:
        safe_name = default_name
    if not safe_name.lower().endswith(extension.lower()):
        safe_name += extension
    return safe_name


def infer_document_type(filename: str) -> str:
    """Infer a document type from filename heuristics."""
    name_lower = filename.lower()

    if "health strategy" in name_lower or "health_strategy" in name_lower:
        return "health_strategy"
    if "economic" in name_lower or "household" in name_lower or "living wage" in name_lower:
        return "economic_indicators"
    if "island project" in name_lower or "capital projects" in name_lower or "regional projects" in name_lower:
        return "island_projects"
    if "news update" in name_lower or "press release" in name_lower or "announcement" in name_lower:
        return "news_update"
    if "budget communication" in name_lower:
        return "budget_communication"
    if "budget book" in name_lower or (
        "budget" in name_lower and "communication" not in name_lower
    ):
        return "budget_book"
    if "revenue" in name_lower:
        return "revenue_estimates"
    if "capital" in name_lower:
        return "capital_estimates"
    if "mid-year" in name_lower or "mid year" in name_lower:
        return "mid_year_statement"
    if "debt" in name_lower:
        return "debt_report"
    if "sweethearting" in name_lower or (
        "fielding" in name_lower and ("balance" in name_lower or "ballance" in name_lower)
    ):
        return "procurement_report"
    if "gbpa" in name_lower or "arbitration" in name_lower or "award" in name_lower:
        return "legal_ruling"
    return "other"


def extract_fiscal_year(filename: str) -> Optional[str]:
    """Extract a fiscal year from a filename if present."""
    year_patterns = [
        r"20\d{2}[-/]20\d{2}",
        r"20\d{2}[-/]?\d{2}",
    ]

    for pattern in year_patterns:
        match = re.search(pattern, filename)
        if not match:
            continue

        year_str = match.group()
        if "-" in year_str:
            left, right = year_str.split("-", 1)
            if len(right) == 2:
                return f"{left}/{right}"
            return year_str.replace("-", "/")
        if "/" in year_str:
            return year_str
        if len(year_str) == 6:
            return f"{year_str[:4]}/{year_str[4:]}"

    return None


def find_document_by_hash(metadata: dict, file_hash: str) -> Optional[dict]:
    """Return an existing metadata record by hash if present."""
    for doc in metadata.get("documents", []):
        if doc.get("file_hash") == file_hash:
            return doc
    return None


def build_unique_raw_path(filename: str) -> Path:
    """Find a unique path in RAW_DIR for a sanitized filename."""
    raw_path = RAW_DIR / filename
    if not raw_path.exists():
        return raw_path

    base_name = raw_path.stem
    counter = 1
    while raw_path.exists():
        raw_path = RAW_DIR / f"{base_name}_{counter}.pdf"
        counter += 1
    return raw_path


def build_unique_metadata_filename(filename: str) -> str:
    """Build a unique metadata filename across all registered documents."""
    metadata = load_metadata()
    taken = {doc.get("filename") for doc in metadata.get("documents", [])}
    if filename not in taken:
        return filename

    candidate = Path(filename)
    base_name = candidate.stem
    suffix = candidate.suffix
    counter = 1
    next_name = filename
    while next_name in taken:
        next_name = f"{base_name}_{counter}{suffix}"
        counter += 1
    return next_name


def register_document_bytes(
    *,
    content: bytes,
    original_filename: str,
    original_url: str | None = None,
    document_type: str | None = None,
    fiscal_year: str | None = None,
    upload_source: str = "manual",
) -> tuple[dict, bool]:
    """Register a PDF from bytes, returning (document_metadata, created_new)."""
    ensure_document_dirs()

    metadata = load_metadata()
    file_hash = compute_sha256_bytes(content)
    existing = find_document_by_hash(metadata, file_hash)
    if existing:
        existing_path = RAW_DIR / existing["filename"]
        if not existing_path.exists():
            existing_path.write_bytes(content)
        return existing, False

    safe_name = sanitize_filename(original_filename)
    raw_path = build_unique_raw_path(safe_name)
    raw_path.write_bytes(content)

    resolved_document_type = document_type or infer_document_type(original_filename)
    resolved_fiscal_year = fiscal_year or extract_fiscal_year(original_filename)

    doc_meta = {
        "filename": raw_path.name,
        "original_filename": original_filename,
        "original_url": original_url,
        "name": original_filename.replace(".pdf", ""),
        "file_hash": file_hash,
        "downloaded_at": datetime.now().isoformat(),
        "file_size": raw_path.stat().st_size,
        "extraction_status": "pending",
        "document_type": resolved_document_type,
        "fiscal_year": resolved_fiscal_year,
        "upload_source": upload_source,
    }

    metadata.setdefault("documents", []).append(doc_meta)
    save_metadata(metadata)
    return doc_meta, True


def register_structured_document(
    *,
    title: str | None,
    document_type: str,
    structured_data: dict,
    original_url: str | None = None,
    fiscal_year: str | None = None,
    upload_source: str = "structured_api",
    submit_after_upload: bool = False,
    review_notes: str | None = None,
) -> tuple[dict, bool]:
    """Register normalized structured data as a reviewable document record."""
    ensure_document_dirs()

    payload_bytes = json.dumps(structured_data, sort_keys=True).encode("utf-8")
    metadata = load_metadata()
    file_hash = compute_sha256_bytes(payload_bytes)
    existing = find_document_by_hash(metadata, file_hash)
    if existing:
        artifact_path = get_processed_artifact_path(existing["filename"], "normalized")
        if not artifact_path.exists():
            artifact_path.write_text(json.dumps(structured_data, indent=2))
        return existing, False

    title_base = title or structured_data.get("title") or structured_data.get("source_document") or document_type
    safe_name = sanitize_storage_name(title_base, default_name="structured-data", extension=".json")
    filename = build_unique_metadata_filename(safe_name)
    resolved_fiscal_year = fiscal_year or structured_data.get("fiscal_year")
    timestamp = datetime.now().isoformat()

    artifact_payload = {
        **structured_data,
        "document_type": structured_data.get("document_type") or document_type,
        "fiscal_year": structured_data.get("fiscal_year") or resolved_fiscal_year,
        "source_document": structured_data.get("source_document") or filename,
        "normalization_provider": structured_data.get("normalization_provider") or "manual",
        "normalization_model": structured_data.get("normalization_model"),
        "normalized_at": structured_data.get("normalized_at") or timestamp,
    }
    artifact_path = get_processed_artifact_path(filename, "normalized")
    artifact_path.write_text(json.dumps(artifact_payload, indent=2))

    extracted_items = structured_data.get("extracted_items", [])
    review_status = "approved" if submit_after_upload else "pending_review"
    doc_meta = {
        "filename": filename,
        "original_filename": title_base,
        "original_url": original_url,
        "name": title_base.replace(".json", ""),
        "file_hash": file_hash,
        "downloaded_at": timestamp,
        "file_size": len(payload_bytes),
        "extraction_status": "success",
        "chunk_count": 0,
        "document_type": document_type,
        "fiscal_year": resolved_fiscal_year,
        "upload_source": upload_source,
        "normalization_status": "success",
        "normalized_count": len(extracted_items) if isinstance(extracted_items, list) else 0,
        "embedding_status": "waiting_for_processing",
        "embedding_count": 0,
        "review_status": review_status,
        "review_notes": review_notes,
    }
    if submit_after_upload:
        doc_meta["reviewed_at"] = timestamp
        doc_meta["submitted_at"] = timestamp

    metadata.setdefault("documents", []).append(doc_meta)
    save_metadata(metadata)
    return doc_meta, True


def find_document_path(filename: str) -> Optional[Path]:
    """Locate a PDF in RAW_DIR using exact or normalized matching."""
    candidate = RAW_DIR / filename
    if candidate.exists():
        return candidate

    candidate = RAW_DIR / filename.replace("_", " ")
    if candidate.exists():
        return candidate

    candidate = RAW_DIR / filename.replace(" ", "_")
    if candidate.exists():
        return candidate

    normalized_search = filename.lower().replace(" ", "_").replace("_", "")
    for pdf_file in RAW_DIR.glob("*.pdf"):
        normalized_pdf = pdf_file.name.lower().replace(" ", "_").replace("_", "")
        if normalized_pdf == normalized_search or pdf_file.name.lower() == filename.lower():
            return pdf_file
    return None


def get_processed_artifact_path(filename: str, suffix: str) -> Path:
    """Return the processed artifact path for a document filename and suffix."""
    base_name = Path(filename).stem
    return PROCESSED_DIR / f"{base_name}_{suffix}.json"


def load_processed_artifact(filename: str, suffix: str) -> Optional[dict]:
    """Load a processed JSON artifact if it exists on disk."""
    artifact_path = get_processed_artifact_path(filename, suffix)
    if not artifact_path.exists():
        return None

    with open(artifact_path) as file_obj:
        return json.load(file_obj)


def normalize_legacy_uploads() -> None:
    """Copy legacy uploaded PDFs into canonical raw storage when missing.

    Older project flows stored source PDFs in ``data/uploads`` while newer code expects
    canonical files in ``data/raw``. This keeps the existing library usable without
    asking operators to manually move files.
    """
    if not METADATA_FILE.exists():
        return

    metadata = load_metadata()
    for doc in metadata.get("documents", []):
        filename = doc.get("filename")
        if not filename or (RAW_DIR / filename).exists():
            continue

        candidate_names = [
            filename,
            doc.get("original_filename"),
            filename.replace("_", " "),
            filename.replace(" ", "_"),
        ]

        source_path: Path | None = None
        for candidate in candidate_names:
            if not candidate:
                continue
            direct_path = UPLOADS_DIR / candidate
            if direct_path.exists():
                source_path = direct_path
                break

        if source_path is None:
            normalized_target = re.sub(r"[\s_]+", "", filename).lower()
            for upload_file in UPLOADS_DIR.glob("*.pdf"):
                normalized_source = re.sub(r"[\s_]+", "", upload_file.name).lower()
                if normalized_source == normalized_target:
                    source_path = upload_file
                    break

        if source_path is None:
            continue

        shutil.copy2(source_path, RAW_DIR / filename)


def delete_document_storage(filename: str) -> dict[str, int]:
    """Delete a document's stored source file, artifacts, and metadata entry."""
    ensure_document_dirs()

    deleted_source_files = 0
    deleted_processed_files = 0
    deleted_embedding_files = 0
    deleted_metadata_records = 0

    file_path = find_document_path(filename)
    if file_path and file_path.exists():
        file_path.unlink()
        deleted_source_files += 1

    base_name = Path(filename).stem
    for artifact_path in PROCESSED_DIR.glob(f"{base_name}_*"):
        if artifact_path.is_file():
            artifact_path.unlink()
            deleted_processed_files += 1

    for embedding_path in EMBEDDINGS_DIR.glob(f"{base_name}_*"):
        if embedding_path.is_file():
            embedding_path.unlink()
            deleted_embedding_files += 1

    metadata = load_metadata()
    original_count = len(metadata.get("documents", []))
    metadata["documents"] = [
        doc for doc in metadata.get("documents", []) if doc.get("filename") != filename
    ]
    deleted_metadata_records = original_count - len(metadata["documents"])
    save_metadata(metadata)

    return {
        "deleted_source_files": deleted_source_files,
        "deleted_processed_files": deleted_processed_files,
        "deleted_embedding_files": deleted_embedding_files,
        "deleted_metadata_records": deleted_metadata_records,
    }

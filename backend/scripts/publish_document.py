#!/usr/bin/env python3
"""Publish approved documents into the live finance tables from the CLI.

This mirrors the admin "Review -> Approve -> Publish" endpoint
(`POST /api/v1/documents/{filename}/publish`) but runs headless against
whatever database `DATABASE_URL` points at, so production publishes do not
require the admin UI.

Usage (run from the backend/ directory):

    # Publish a single approved document by filename
    DATABASE_URL=postgresql://user:pass@host:5432/db \
        python scripts/publish_document.py "FY2026-27_Draft_Estimates_of_Revenue_and_Expenditure.pdf"

    # Publish every approved-but-unpublished document
    DATABASE_URL=... python scripts/publish_document.py --all

    # Preview what would publish without writing to the database
    DATABASE_URL=... python scripts/publish_document.py --all --dry-run

Notes:
    - The document must already be extracted (`extraction_status == "success"`)
      and approved (review status `approved`) in `data/document_metadata.json`.
    - Normalized artifacts must exist in `data/processed/` for finance rows to
      be written; otherwise only the source document record is published.
    - On success, `publish_status`/`published_at`/`publish_result` are written
      back to the metadata file, matching the admin endpoint behavior.
"""
import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Allow running as `python scripts/publish_document.py` from the backend dir.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.database import AsyncSessionLocal  # noqa: E402
from app.services.document_ingestion import (  # noqa: E402
    load_metadata,
    save_metadata,
)
from app.services.finance_publisher import (  # noqa: E402
    publish_document_to_finance_tables,
)


def _resolve_review_status(doc: dict) -> str:
    """Derive review status the same way the documents API does."""
    explicit = doc.get("review_status")
    if explicit:
        return explicit
    if doc.get("submitted_at"):
        return "approved"
    if doc.get("extraction_status") == "success":
        return "pending_review"
    return "waiting_for_processing"


def _is_publishable(doc: dict) -> tuple[bool, str]:
    """Return (ok, reason) describing whether a document can be published."""
    if _resolve_review_status(doc) != "approved":
        return False, "not approved (review status must be 'approved')"
    if doc.get("extraction_status") != "success":
        return False, "extraction not successful"
    return True, "ok"


def _select_documents(
    metadata: dict, filename: str | None, publish_all: bool
) -> list[dict]:
    documents = metadata.get("documents", [])
    if filename:
        target = next((d for d in documents if d.get("filename") == filename), None)
        if target is None:
            raise SystemExit(f"Document '{filename}' not found in metadata.")
        return [target]

    if publish_all:
        selected = []
        for doc in documents:
            ok, _ = _is_publishable(doc)
            if ok and doc.get("publish_status") != "success":
                selected.append(doc)
        return selected

    raise SystemExit("Provide a filename or use --all.")


async def _publish_one(doc: dict, dry_run: bool) -> dict:
    filename = doc.get("filename")
    ok, reason = _is_publishable(doc)
    if not ok:
        return {"filename": filename, "status": "skipped", "reason": reason}

    if dry_run:
        return {"filename": filename, "status": "dry-run", "reason": "would publish"}

    async with AsyncSessionLocal() as session:
        result = await publish_document_to_finance_tables(session, doc_meta=doc)
        await session.commit()

    doc["publish_status"] = result.status
    doc["published_at"] = datetime.now().isoformat()
    doc["publish_result"] = result.as_dict()
    return {
        "filename": filename,
        "status": result.status,
        "published_records": result.published_records,
        "warnings": result.warnings,
    }


async def _run(filename: str | None, publish_all: bool, dry_run: bool) -> int:
    metadata = load_metadata()
    targets = _select_documents(metadata, filename, publish_all)

    if not targets:
        print("Nothing to publish (no approved, unpublished documents found).")
        return 0

    print(f"Publishing {len(targets)} document(s){' (dry run)' if dry_run else ''}:")
    results = []
    for doc in targets:
        outcome = await _publish_one(doc, dry_run)
        results.append(outcome)
        line = f"  - {outcome['filename']}: {outcome['status']}"
        if outcome.get("reason"):
            line += f" ({outcome['reason']})"
        if outcome.get("published_records"):
            line += f" {outcome['published_records']}"
        print(line)
        for warning in outcome.get("warnings") or []:
            print(f"      warning: {warning}")

    if not dry_run:
        save_metadata(metadata)
        print("Metadata updated with publish status.")

    failed = [r for r in results if r["status"] not in {"success", "partial_success", "dry-run", "skipped"}]
    return 1 if failed else 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish approved documents into finance tables.")
    parser.add_argument("filename", nargs="?", help="Document filename to publish (from metadata).")
    parser.add_argument("--all", action="store_true", help="Publish all approved, unpublished documents.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would publish without writing.")
    args = parser.parse_args()

    exit_code = asyncio.run(_run(args.filename, args.all, args.dry_run))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

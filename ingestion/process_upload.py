"""Bahamas Open Data - Manual Upload Processor."""
from pathlib import Path
from typing import Optional
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.services.document_ingestion import (
    UPLOADS_DIR,
    ensure_document_dirs,
    register_document_bytes,
)


def process_uploaded_pdf(pdf_filename: str, document_type: Optional[str] = None, fiscal_year: Optional[str] = None) -> dict:
    """
    Process a manually uploaded PDF.
    
    Args:
        pdf_filename: Name of the PDF file in uploads directory
        document_type: Optional document type override
        fiscal_year: Optional fiscal year override
    
    Returns:
        Document metadata dict
    """
    ensure_document_dirs()

    upload_path = UPLOADS_DIR / pdf_filename
    if not upload_path.exists():
        raise FileNotFoundError(f"PDF not found in uploads: {pdf_filename}")

    doc_meta, created = register_document_bytes(
        content=upload_path.read_bytes(),
        original_filename=pdf_filename,
        document_type=document_type,
        fiscal_year=fiscal_year,
        upload_source="manual",
    )

    if created:
        print(f"✓ Copied to raw directory: {doc_meta['filename']}")
        print(f"✓ Registered in metadata: {doc_meta['filename']}")
        print(f"  Type: {doc_meta['document_type']}")
        if doc_meta.get("fiscal_year"):
            print(f"  Fiscal Year: {doc_meta['fiscal_year']}")
    else:
        print(f"⊙ Document already exists (hash match): {pdf_filename}")

    return doc_meta


def main():
    """Main entry point for processing uploads."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python process_upload.py <pdf_filename> [document_type] [fiscal_year]")
        print("\nExample:")
        print('  python process_upload.py "Bahamas National Health Strategy FINAL (08Dec2025).pdf"')
        print('  python process_upload.py "document.pdf" health_strategy "2026/30"')
        sys.exit(1)
    
    pdf_filename = sys.argv[1]
    document_type = sys.argv[2] if len(sys.argv) > 2 else None
    fiscal_year = sys.argv[3] if len(sys.argv) > 3 else None
    
    print("🇧🇸 Bahamas Open Data - Manual Upload Processor")
    print("=" * 40)
    
    try:
        doc_meta = process_uploaded_pdf(pdf_filename, document_type, fiscal_year)
        print(f"\n✅ Successfully processed: {doc_meta['filename']}")
        print(f"\nNext steps:")
        print(f"  1. Run parser.py to extract text and tables")
        print(f"  2. Run embeddings.py to create RAG embeddings")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

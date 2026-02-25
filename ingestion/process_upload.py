"""
Bahamas Open Data - Manual Upload Processor
Processes manually uploaded PDFs from the uploads directory.
"""
import os
import hashlib
import json
import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional


# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
RAW_DIR = DATA_DIR / "raw"
METADATA_FILE = DATA_DIR / "document_metadata.json"


def ensure_dirs():
    """Create necessary directories."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def compute_file_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_metadata() -> dict:
    """Load existing document metadata."""
    if METADATA_FILE.exists():
        with open(METADATA_FILE) as f:
            return json.load(f)
    return {"documents": []}


def save_metadata(metadata: dict):
    """Save document metadata."""
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=2, default=str)


def infer_document_type(filename: str) -> str:
    """Infer document type from filename."""
    name_lower = filename.lower()
    
    if "health strategy" in name_lower or "health_strategy" in name_lower:
        return "health_strategy"
    elif "budget communication" in name_lower:
        return "budget_communication"
    elif "budget book" in name_lower or ("budget" in name_lower and "communication" not in name_lower):
        return "budget_book"
    elif "revenue" in name_lower:
        return "revenue_estimates"
    elif "capital" in name_lower:
        return "capital_estimates"
    elif "mid-year" in name_lower or "mid year" in name_lower:
        return "mid_year_statement"
    elif "debt" in name_lower:
        return "debt_report"
    else:
        return "other"


def extract_fiscal_year(filename: str) -> Optional[str]:
    """Extract fiscal year from filename."""
    # Look for patterns like "2026-2030", "2026/30", "2026-30"
    year_patterns = [
        r"20\d{2}[-/]20\d{2}",  # 2026-2030, 2026/2030
        r"20\d{2}[-/]?\d{2}",   # 2026-30, 2026/30, 202630
    ]
    
    for pattern in year_patterns:
        match = re.search(pattern, filename)
        if match:
            year_str = match.group()
            # Normalize to format like "2026/30"
            if "-" in year_str:
                parts = year_str.split("-")
                if len(parts) == 2:
                    if len(parts[1]) == 2:
                        return f"{parts[0]}/{parts[1]}"
                    else:
                        return year_str.replace("-", "/")
            elif "/" in year_str:
                return year_str
            elif len(year_str) == 6:
                return f"{year_str[:4]}/{year_str[4:]}"
    
    return None


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
    ensure_dirs()
    
    upload_path = UPLOADS_DIR / pdf_filename
    if not upload_path.exists():
        raise FileNotFoundError(f"PDF not found in uploads: {pdf_filename}")
    
    # Load existing metadata
    metadata = load_metadata()
    existing_hashes = {doc["file_hash"] for doc in metadata["documents"] if "file_hash" in doc}
    
    # Compute hash of uploaded file
    file_hash = compute_file_hash(upload_path)
    
    # Check if already processed
    if file_hash in existing_hashes:
        print(f"⊙ Document already exists (hash match): {pdf_filename}")
        for doc in metadata["documents"]:
            if doc.get("file_hash") == file_hash:
                return doc
    
    # Create safe filename
    safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in pdf_filename)
    if not safe_name.endswith(".pdf"):
        safe_name += ".pdf"
    
    # Move to raw directory
    raw_path = RAW_DIR / safe_name
    if raw_path.exists():
        # If file exists but hash doesn't match, create unique name
        base_name = raw_path.stem
        counter = 1
        while raw_path.exists():
            raw_path = RAW_DIR / f"{base_name}_{counter}.pdf"
            counter += 1
        safe_name = raw_path.name
    
    shutil.copy2(upload_path, raw_path)
    print(f"✓ Copied to raw directory: {safe_name}")
    
    # Infer document type if not provided
    if not document_type:
        document_type = infer_document_type(pdf_filename)
    
    # Extract fiscal year if not provided
    if not fiscal_year:
        fiscal_year = extract_fiscal_year(pdf_filename)
    
    # Create metadata entry
    doc_meta = {
        "filename": safe_name,
        "original_filename": pdf_filename,
        "original_url": None,  # Manual upload, no URL
        "name": pdf_filename.replace(".pdf", ""),
        "file_hash": file_hash,
        "downloaded_at": datetime.now().isoformat(),
        "file_size": raw_path.stat().st_size,
        "extraction_status": "pending",
        "document_type": document_type,
        "fiscal_year": fiscal_year,
        "upload_source": "manual",
    }
    
    metadata["documents"].append(doc_meta)
    save_metadata(metadata)
    
    print(f"✓ Registered in metadata: {safe_name}")
    print(f"  Type: {document_type}")
    if fiscal_year:
        print(f"  Fiscal Year: {fiscal_year}")
    
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


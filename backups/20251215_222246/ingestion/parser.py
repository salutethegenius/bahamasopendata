"""
Bahamas Open Data - PDF Parser
Extracts tables and text from budget documents.
"""
import os
import re
import json
from pathlib import Path
from typing import Optional
from datetime import datetime
import pdfplumber
import pandas as pd
from tqdm import tqdm


# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
METADATA_FILE = DATA_DIR / "document_metadata.json"

# Ministry name normalization
MINISTRY_ALIASES = {
    "ministry of education": "MOE",
    "education": "MOE",
    "ministry of health": "MOH",
    "health": "MOH",
    "ministry of national security": "MNS",
    "national security": "MNS",
    "ministry of works": "MOW",
    "works": "MOW",
    "ministry of works and utilities": "MOW",
    "ministry of finance": "MOF",
    "finance": "MOF",
    "ministry of tourism": "MOT",
    "tourism": "MOT",
    "ministry of social services": "MSS",
    "social services": "MSS",
    "ministry of agriculture": "MOA",
    "agriculture": "MOA",
    "ministry of environment": "MOENV",
    "environment": "MOENV",
    "office of the prime minister": "PMO",
    "prime minister": "PMO",
}


def ensure_dirs():
    """Create necessary directories."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def load_metadata() -> dict:
    """Load document metadata."""
    if METADATA_FILE.exists():
        with open(METADATA_FILE) as f:
            return json.load(f)
    return {"documents": []}


def save_metadata(metadata: dict):
    """Save document metadata."""
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=2, default=str)


def normalize_ministry_name(name: str) -> Optional[str]:
    """Normalize ministry names to standard codes."""
    if not name:
        return None
    name_lower = name.lower().strip()
    for pattern, code in MINISTRY_ALIASES.items():
        if pattern in name_lower:
            return code
    return None


def clean_currency(value: str) -> Optional[float]:
    """Parse currency values from various formats."""
    if not value or not isinstance(value, str):
        return None
    
    # Remove currency symbols and whitespace
    cleaned = re.sub(r'[$B\s,]', '', value.strip())
    
    # Handle parentheses for negative numbers
    if cleaned.startswith('(') and cleaned.endswith(')'):
        cleaned = '-' + cleaned[1:-1]
    
    try:
        return float(cleaned)
    except ValueError:
        return None


def extract_text_from_pdf(pdf_path: Path) -> list[dict]:
    """Extract all text from a PDF by page."""
    pages = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                pages.append({
                    "page_number": i + 1,
                    "text": text,
                    "char_count": len(text),
                })
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
    
    return pages


def extract_tables_from_pdf(pdf_path: Path) -> list[dict]:
    """Extract tables from a PDF."""
    all_tables = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(tqdm(pdf.pages, desc="Extracting tables", leave=False)):
                tables = page.extract_tables()
                
                for j, table in enumerate(tables):
                    if not table or len(table) < 2:
                        continue
                    
                    # Convert to DataFrame for easier processing
                    df = pd.DataFrame(table[1:], columns=table[0])
                    
                    # Skip empty or invalid tables
                    if df.empty or len(df.columns) < 2:
                        continue
                    
                    all_tables.append({
                        "page_number": i + 1,
                        "table_index": j,
                        "columns": list(df.columns),
                        "row_count": len(df),
                        "data": df.to_dict(orient="records"),
                    })
    except Exception as e:
        print(f"Error extracting tables from {pdf_path}: {e}")
    
    return all_tables


def parse_budget_table(table_data: dict) -> Optional[dict]:
    """Parse a budget allocation table into structured data."""
    columns = [str(c).lower() if c else "" for c in table_data.get("columns", [])]
    rows = table_data.get("data", [])
    
    # Look for common budget table patterns
    # Columns might be: Item, Description, Amount, Previous Year, etc.
    
    amount_col = None
    name_col = None
    
    for i, col in enumerate(columns):
        if any(term in col for term in ["amount", "allocation", "budget", "estimate", "total"]):
            amount_col = i
        if any(term in col for term in ["item", "description", "name", "head", "ministry"]):
            name_col = i
    
    if amount_col is None or name_col is None:
        return None
    
    parsed_items = []
    for row in rows:
        values = list(row.values())
        if len(values) <= max(amount_col, name_col):
            continue
        
        name = str(values[name_col]) if values[name_col] else ""
        amount = clean_currency(str(values[amount_col]) if values[amount_col] else "")
        
        if name and amount:
            ministry_code = normalize_ministry_name(name)
            parsed_items.append({
                "name": name.strip(),
                "amount": amount,
                "ministry_code": ministry_code,
            })
    
    if not parsed_items:
        return None
    
    return {
        "items": parsed_items,
        "page_number": table_data["page_number"],
        "table_index": table_data["table_index"],
    }


def process_document(doc_meta: dict) -> dict:
    """Process a single document."""
    filename = doc_meta["filename"]
    pdf_path = RAW_DIR / filename
    
    if not pdf_path.exists():
        print(f"⚠ File not found: {filename}")
        return {"status": "file_not_found"}
    
    print(f"\n📄 Processing: {filename}")
    
    # Extract text
    pages = extract_text_from_pdf(pdf_path)
    
    # Extract tables
    tables = extract_tables_from_pdf(pdf_path)
    
    # Parse budget tables
    parsed_budgets = []
    for table in tables:
        parsed = parse_budget_table(table)
        if parsed:
            parsed_budgets.append(parsed)
    
    # Save processed data
    base_name = pdf_path.stem
    
    # Save full text
    text_file = PROCESSED_DIR / f"{base_name}_text.json"
    with open(text_file, "w") as f:
        json.dump({
            "source": filename,
            "pages": pages,
            "extracted_at": datetime.now().isoformat(),
        }, f, indent=2)
    
    # Save tables
    tables_file = PROCESSED_DIR / f"{base_name}_tables.json"
    with open(tables_file, "w") as f:
        json.dump({
            "source": filename,
            "tables": tables,
            "parsed_budgets": parsed_budgets,
            "extracted_at": datetime.now().isoformat(),
        }, f, indent=2)
    
    # Save as CSV if we have budget data
    if parsed_budgets:
        all_items = []
        for budget in parsed_budgets:
            for item in budget["items"]:
                all_items.append({
                    **item,
                    "source_page": budget["page_number"],
                    "source_file": filename,
                })
        
        if all_items:
            csv_file = PROCESSED_DIR / f"{base_name}_budget_items.csv"
            df = pd.DataFrame(all_items)
            df.to_csv(csv_file, index=False)
            print(f"  ✓ Saved {len(all_items)} budget items to CSV")
    
    return {
        "status": "success",
        "pages": len(pages),
        "tables": len(tables),
        "parsed_budgets": len(parsed_budgets),
        "total_text_chars": sum(p["char_count"] for p in pages),
    }


def create_document_chunks(doc_meta: dict, chunk_size: int = 1000) -> list[dict]:
    """Create text chunks for RAG embedding."""
    filename = doc_meta["filename"]
    base_name = Path(filename).stem
    text_file = PROCESSED_DIR / f"{base_name}_text.json"
    
    if not text_file.exists():
        return []
    
    with open(text_file) as f:
        data = json.load(f)
    
    chunks = []
    chunk_id = 0
    
    for page in data["pages"]:
        text = page["text"]
        page_num = page["page_number"]
        
        # Split into paragraphs first
        paragraphs = text.split("\n\n")
        
        current_chunk = ""
        for para in paragraphs:
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk.strip():
                    chunks.append({
                        "id": f"{base_name}_chunk_{chunk_id}",
                        "document": filename,
                        "page_number": page_num,
                        "content": current_chunk.strip(),
                        "char_count": len(current_chunk),
                    })
                    chunk_id += 1
                current_chunk = para + "\n\n"
        
        # Don't forget the last chunk
        if current_chunk.strip():
            chunks.append({
                "id": f"{base_name}_chunk_{chunk_id}",
                "document": filename,
                "page_number": page_num,
                "content": current_chunk.strip(),
                "char_count": len(current_chunk),
            })
            chunk_id += 1
    
    # Save chunks
    chunks_file = PROCESSED_DIR / f"{base_name}_chunks.json"
    with open(chunks_file, "w") as f:
        json.dump({
            "source": filename,
            "chunk_count": len(chunks),
            "chunks": chunks,
            "created_at": datetime.now().isoformat(),
        }, f, indent=2)
    
    return chunks


def main():
    """Main parser entry point."""
    print("🇧🇸 Bahamas Open Data - Document Parser")
    print("=" * 40)
    
    ensure_dirs()
    metadata = load_metadata()
    
    if not metadata.get("documents"):
        print("No documents found. Run scraper.py first.")
        return
    
    # Process each document
    for doc in tqdm(metadata["documents"], desc="Processing documents"):
        if doc.get("extraction_status") == "completed":
            print(f"⊙ Skipping (already processed): {doc['filename']}")
            continue
        
        result = process_document(doc)
        doc["extraction_status"] = result["status"]
        doc["extraction_result"] = result
        doc["extracted_at"] = datetime.now().isoformat()
        
        # Create chunks for RAG
        if result["status"] == "success":
            chunks = create_document_chunks(doc)
            doc["chunk_count"] = len(chunks)
            print(f"  ✓ Created {len(chunks)} chunks for RAG")
        
        save_metadata(metadata)
    
    # Summary
    print("\n" + "=" * 40)
    print("✅ Processing complete!")
    
    successful = sum(1 for d in metadata["documents"] if d.get("extraction_status") == "success")
    print(f"   Processed: {successful}/{len(metadata['documents'])} documents")
    print(f"   Output directory: {PROCESSED_DIR}")


if __name__ == "__main__":
    main()


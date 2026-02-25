"""
Bahamas Open Data - Embeddings Pipeline
Creates embeddings for document chunks and indexes them in Pinecone.
"""
import os
import json
from pathlib import Path
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv
import openai
from pinecone import Pinecone, ServerlessSpec
from tqdm import tqdm
import time


# Load environment
load_dotenv()

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
PROCESSED_DIR = DATA_DIR / "processed"
EMBEDDINGS_DIR = DATA_DIR / "embeddings"
METADATA_FILE = DATA_DIR / "document_metadata.json"

# OpenAI settings
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536

# Pinecone settings
PINECONE_INDEX = os.getenv("PINECONE_INDEX_NAME", "national-pulse")


def ensure_dirs():
    """Create necessary directories."""
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)


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


def get_openai_client() -> openai.OpenAI:
    """Get OpenAI client."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in environment")
    return openai.OpenAI(api_key=api_key)


def get_pinecone_client() -> Pinecone:
    """Get Pinecone client."""
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY not set in environment")
    return Pinecone(api_key=api_key)


def create_embeddings(texts: list[str], client: openai.OpenAI) -> list[list[float]]:
    """Create embeddings for a batch of texts."""
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]


def init_pinecone_index(pc: Pinecone) -> any:
    """Initialize Pinecone index."""
    # Check if index exists
    existing_indexes = pc.list_indexes()
    index_names = [idx.name for idx in existing_indexes]
    
    if PINECONE_INDEX not in index_names:
        print(f"Creating Pinecone index: {PINECONE_INDEX}")
        pc.create_index(
            name=PINECONE_INDEX,
            dimension=EMBEDDING_DIMENSIONS,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region=os.getenv("PINECONE_ENVIRONMENT", "us-east-1"),
            ),
        )
        # Wait for index to be ready
        time.sleep(10)
    
    return pc.Index(PINECONE_INDEX)


def sanitize_metadata_string(text: str) -> str:
    """Sanitize string for Pinecone metadata by replacing problematic Unicode characters.
    
    Pinecone's HTTP client requires Latin-1 encoding, so we must ensure all strings
    are ASCII-compatible. This function replaces common Unicode characters with ASCII
    equivalents and removes any remaining non-ASCII characters.
    """
    if not text or text is None:
        return ""
    
    # Ensure it's a string
    if not isinstance(text, str):
        text = str(text)
    
    # Replace common Unicode characters with ASCII equivalents
    replacements = {
        '\u2013': '-',  # en dash
        '\u2014': '--',  # em dash
        '\u2018': "'",  # left single quotation mark
        '\u2019': "'",  # right single quotation mark
        '\u201C': '"',  # left double quotation mark
        '\u201D': '"',  # right double quotation mark
        '\u2026': '...',  # ellipsis
        '\u00A0': ' ',  # non-breaking space
        '\u2022': '*',  # bullet point
        '\u2023': '*',  # triangular bullet
        '\u25E6': '*',  # white bullet
        '\u2043': '-',  # hyphen bullet
        '\u2219': '*',  # bullet operator
        '\u00B7': '*',  # middle dot
        '\u00AD': '',   # soft hyphen (remove)
        '\u2009': ' ',  # thin space
        '\u200A': ' ',  # hair space
        '\u200B': '',   # zero-width space (remove)
        '\u200C': '',   # zero-width non-joiner (remove)
        '\u200D': '',   # zero-width joiner (remove)
        '\uFEFF': '',   # zero-width no-break space (remove)
    }
    
    result = text
    for unicode_char, ascii_char in replacements.items():
        result = result.replace(unicode_char, ascii_char)
    
    # Aggressively remove any remaining non-ASCII characters
    # This ensures the string can be safely encoded in Latin-1 for HTTP requests
    # We use 'ignore' to remove problematic characters rather than raising errors
    result = result.encode('ascii', errors='ignore').decode('ascii')
    
    return result


def load_chunks(doc_meta: dict) -> list[dict]:
    """Load chunks for a document."""
    filename = doc_meta["filename"]
    base_name = Path(filename).stem
    chunks_file = PROCESSED_DIR / f"{base_name}_chunks.json"
    
    if not chunks_file.exists():
        return []
    
    with open(chunks_file) as f:
        data = json.load(f)
    
    return data.get("chunks", [])


def process_document_embeddings(
    doc_meta: dict,
    openai_client: openai.OpenAI,
    pinecone_index: any,
    batch_size: int = 50,
) -> dict:
    """Create embeddings for a document and upload to Pinecone."""
    chunks = load_chunks(doc_meta)
    
    if not chunks:
        return {"status": "no_chunks", "embedded": 0}
    
    filename = doc_meta["filename"]
    base_name = Path(filename).stem
    
    print(f"\n📝 Embedding: {filename} ({len(chunks)} chunks)")
    
    all_embeddings = []
    
    # Process in batches
    for i in tqdm(range(0, len(chunks), batch_size), desc="Creating embeddings"):
        batch = chunks[i:i + batch_size]
        texts = [c["content"] for c in batch]
        
        try:
            embeddings = create_embeddings(texts, openai_client)
            
            for j, emb in enumerate(embeddings):
                chunk = batch[j]
                # Sanitize all string fields for Pinecone metadata
                # Truncate content first, then sanitize to ensure we stay within limits
                raw_content = chunk["content"][:1000]
                content_snippet = sanitize_metadata_string(raw_content)
                
                # Sanitize chunk ID as well (in case it contains special chars)
                chunk_id = sanitize_metadata_string(chunk["id"])
                
                all_embeddings.append({
                    "id": chunk_id,
                    "embedding": emb,
                    "metadata": {
                        "document": sanitize_metadata_string(filename),
                        "page_number": int(chunk["page_number"]),  # Ensure it's an int, not string
                        "content": content_snippet,  # Truncate and sanitize for Pinecone metadata limit
                        "fiscal_year": sanitize_metadata_string(str(doc_meta.get("fiscal_year", "") or "")),
                        "document_type": sanitize_metadata_string(str(doc_meta.get("document_type", "") or "")),
                    },
                })
        except Exception as e:
            print(f"  ⚠ Error embedding batch: {e}")
            continue
        
        # Rate limiting
        time.sleep(0.5)
    
    # Save embeddings locally
    emb_file = EMBEDDINGS_DIR / f"{base_name}_embeddings.json"
    with open(emb_file, "w") as f:
        json.dump({
            "source": filename,
            "embedding_count": len(all_embeddings),
            "model": EMBEDDING_MODEL,
            "created_at": datetime.now().isoformat(),
            # Don't save actual embeddings to JSON (too large), just metadata
            "chunk_ids": [e["id"] for e in all_embeddings],
        }, f, indent=2)
    
    # Upload to Pinecone
    print(f"  📤 Uploading {len(all_embeddings)} vectors to Pinecone...")
    
    vectors_to_upsert = [
        {
            "id": e["id"],
            "values": e["embedding"],
            "metadata": e["metadata"],
        }
        for e in all_embeddings
    ]
    
    # Upsert in batches
    successful_uploads = 0
    failed_batches = []
    for i in range(0, len(vectors_to_upsert), 100):
        batch = vectors_to_upsert[i:i + 100]
        batch_num = (i // 100) + 1
        try:
            pinecone_index.upsert(vectors=batch)
            successful_uploads += len(batch)
        except Exception as e:
            failed_batches.append((batch_num, str(e)))
            print(f"  ⚠ Error upserting batch {batch_num}: {e}")
    
    if failed_batches:
        print(f"  ⚠ {len(failed_batches)} batch(es) failed, {successful_uploads}/{len(all_embeddings)} vectors uploaded")
    else:
        print(f"  ✓ Successfully uploaded {successful_uploads} vectors")
    
    return {
        "status": "success",
        "embedded": len(all_embeddings),
    }


def main():
    """Main embeddings pipeline entry point."""
    print("🇧🇸 Bahamas Open Data - Embeddings Pipeline")
    print("=" * 40)
    
    ensure_dirs()
    
    # Initialize clients
    try:
        openai_client = get_openai_client()
        pinecone_client = get_pinecone_client()
        pinecone_index = init_pinecone_index(pinecone_client)
    except ValueError as e:
        print(f"❌ {e}")
        print("   Please set OPENAI_API_KEY and PINECONE_API_KEY in environment or .env file")
        return
    
    metadata = load_metadata()
    
    if not metadata.get("documents"):
        print("No documents found. Run scraper.py and parser.py first.")
        return
    
    # Process each document
    total_embedded = 0
    for doc in metadata["documents"]:
        if doc.get("embedding_status") == "completed":
            print(f"⊙ Skipping (already embedded): {doc['filename']}")
            continue
        
        if doc.get("extraction_status") != "success":
            print(f"⊙ Skipping (not extracted): {doc['filename']}")
            continue
        
        result = process_document_embeddings(doc, openai_client, pinecone_index)
        doc["embedding_status"] = result["status"]
        doc["embedding_count"] = result.get("embedded", 0)
        doc["embedded_at"] = datetime.now().isoformat()
        total_embedded += result.get("embedded", 0)
        
        save_metadata(metadata)
    
    # Summary
    print("\n" + "=" * 40)
    print("✅ Embedding complete!")
    print(f"   Total vectors created: {total_embedded}")
    print(f"   Pinecone index: {PINECONE_INDEX}")


if __name__ == "__main__":
    main()


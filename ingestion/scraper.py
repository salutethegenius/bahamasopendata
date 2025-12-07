"""
Bahamas Open Data - Budget Document Scraper
Downloads official budget documents from Bahamas government sources.
"""
import os
import hashlib
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional
import httpx
from playwright.async_api import async_playwright
from tqdm import tqdm
import json


# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
METADATA_FILE = DATA_DIR / "document_metadata.json"

# Official sources
BUDGET_SITE = "https://www.bahamasbudget.gov.bs"
CENTRAL_BANK = "https://www.centralbankbahamas.com"

# Known document URLs (updated annually)
KNOWN_DOCUMENTS = [
    {
        "name": "Budget Communication 2024-25",
        "url": f"{BUDGET_SITE}/budget-documents/budget-communication/",
        "type": "budget_communication",
        "fiscal_year": "2024/25",
    },
    {
        "name": "Budget Book 2024-25",
        "url": f"{BUDGET_SITE}/budget-documents/budget-book/",
        "type": "budget_book",
        "fiscal_year": "2024/25",
    },
    {
        "name": "Revenue Estimates 2024-25",
        "url": f"{BUDGET_SITE}/budget-documents/revenue-estimates/",
        "type": "revenue_estimates",
        "fiscal_year": "2024/25",
    },
    {
        "name": "Capital Estimates 2024-25",
        "url": f"{BUDGET_SITE}/budget-documents/capital-estimates/",
        "type": "capital_estimates",
        "fiscal_year": "2024/25",
    },
]


def ensure_dirs():
    """Create necessary directories."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)


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


async def download_pdf(url: str, filepath: Path, session: httpx.AsyncClient) -> bool:
    """Download a PDF file."""
    try:
        response = await session.get(url, follow_redirects=True, timeout=60.0)
        response.raise_for_status()
        
        with open(filepath, "wb") as f:
            f.write(response.content)
        
        print(f"✓ Downloaded: {filepath.name}")
        return True
    except Exception as e:
        print(f"✗ Failed to download {url}: {e}")
        return False


async def scrape_budget_site():
    """Scrape the official budget site for PDF links."""
    pdf_links = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Navigate to the budget documents page
            await page.goto(f"{BUDGET_SITE}/budget-documents/", timeout=30000)
            await page.wait_for_load_state("networkidle")
            
            # Find all PDF links
            links = await page.query_selector_all('a[href$=".pdf"]')
            
            for link in links:
                href = await link.get_attribute("href")
                text = await link.text_content()
                
                if href:
                    # Make URL absolute
                    if not href.startswith("http"):
                        href = f"{BUDGET_SITE}{href}" if href.startswith("/") else f"{BUDGET_SITE}/{href}"
                    
                    pdf_links.append({
                        "url": href,
                        "name": text.strip() if text else Path(href).stem,
                    })
            
            print(f"Found {len(pdf_links)} PDF links on budget site")
            
        except Exception as e:
            print(f"Error scraping budget site: {e}")
        finally:
            await browser.close()
    
    return pdf_links


async def download_documents(pdf_links: list[dict]):
    """Download all discovered PDF documents."""
    ensure_dirs()
    metadata = load_metadata()
    existing_hashes = {doc["file_hash"] for doc in metadata["documents"] if "file_hash" in doc}
    
    async with httpx.AsyncClient() as session:
        for pdf in tqdm(pdf_links, desc="Downloading documents"):
            url = pdf["url"]
            name = pdf.get("name", Path(url).stem)
            
            # Create safe filename
            safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in name)
            filename = f"{safe_name}.pdf"
            filepath = RAW_DIR / filename
            
            # Check if already downloaded
            if filepath.exists():
                file_hash = compute_file_hash(filepath)
                if file_hash in existing_hashes:
                    print(f"⊙ Skipping (already exists): {filename}")
                    continue
            
            # Download
            success = await download_pdf(url, filepath, session)
            
            if success:
                file_hash = compute_file_hash(filepath)
                
                # Add to metadata
                doc_meta = {
                    "filename": filename,
                    "original_url": url,
                    "name": name,
                    "file_hash": file_hash,
                    "downloaded_at": datetime.now().isoformat(),
                    "file_size": filepath.stat().st_size,
                    "extraction_status": "pending",
                }
                
                # Infer document type and fiscal year from name
                name_lower = name.lower()
                if "budget communication" in name_lower:
                    doc_meta["document_type"] = "budget_communication"
                elif "budget book" in name_lower:
                    doc_meta["document_type"] = "budget_book"
                elif "revenue" in name_lower:
                    doc_meta["document_type"] = "revenue_estimates"
                elif "capital" in name_lower:
                    doc_meta["document_type"] = "capital_estimates"
                elif "mid-year" in name_lower or "mid year" in name_lower:
                    doc_meta["document_type"] = "mid_year_statement"
                elif "debt" in name_lower:
                    doc_meta["document_type"] = "debt_report"
                else:
                    doc_meta["document_type"] = "other"
                
                # Extract fiscal year if present
                import re
                year_match = re.search(r"20\d{2}[-/]?2?\d{1,2}", name)
                if year_match:
                    year_str = year_match.group()
                    if "-" in year_str or "/" in year_str:
                        doc_meta["fiscal_year"] = year_str.replace("-", "/")
                    elif len(year_str) == 6:
                        doc_meta["fiscal_year"] = f"{year_str[:4]}/{year_str[4:]}"
                
                metadata["documents"].append(doc_meta)
                save_metadata(metadata)


async def main():
    """Main scraper entry point."""
    print("🇧🇸 Bahamas Open Data - Document Scraper")
    print("=" * 40)
    
    # Ensure directories exist
    ensure_dirs()
    
    # Scrape the budget site for PDF links
    print("\n📥 Scanning official budget site...")
    pdf_links = await scrape_budget_site()
    
    if not pdf_links:
        print("No PDF links found. Using known document list as fallback.")
        # Use known documents as fallback
        pdf_links = [{"url": doc["url"], "name": doc["name"]} for doc in KNOWN_DOCUMENTS]
    
    # Download documents
    print(f"\n📄 Downloading {len(pdf_links)} documents...")
    await download_documents(pdf_links)
    
    # Summary
    metadata = load_metadata()
    print(f"\n✅ Complete! {len(metadata['documents'])} documents in database.")
    print(f"   Documents stored in: {RAW_DIR}")


if __name__ == "__main__":
    asyncio.run(main())


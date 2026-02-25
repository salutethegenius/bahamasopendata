"""Document serving API endpoints."""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, Response
from pathlib import Path
import os

router = APIRouter()

# Path to data directory (absolute path)
DATA_DIR = Path("/home/ubuntu/apps/bahamasopendata/data/raw")


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
    # Decode URL encoding
    from urllib.parse import unquote
    filename = unquote(filename)
    
    # Try to find the file - check both with and without underscores
    file_path = None
    
    # First try exact match
    if (DATA_DIR / filename).exists():
        file_path = DATA_DIR / filename
    # Try with underscores replaced by spaces
    elif (DATA_DIR / filename.replace('_', ' ')).exists():
        file_path = DATA_DIR / filename.replace('_', ' ')
    # Try with spaces replaced by underscores
    elif (DATA_DIR / filename.replace(' ', '_')).exists():
        file_path = DATA_DIR / filename.replace(' ', '_')
    else:
        # List all PDFs and try fuzzy match
        for pdf_file in DATA_DIR.glob("*.pdf"):
            # Compare normalized names (ignore case, spaces, underscores)
            normalized_pdf = pdf_file.name.lower().replace(' ', '_').replace('_', '')
            normalized_search = filename.lower().replace(' ', '_').replace('_', '')
            if normalized_pdf == normalized_search or pdf_file.name.lower() == filename.lower():
                file_path = pdf_file
                break
    
    if not file_path or not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Document '{filename}' not found. Available: {[f.name for f in DATA_DIR.glob('*.pdf')]}"
        )
    
    # Return PDF file
    if page:
        # For PDFs with page numbers, we can use a data URI or return the file
        # Most browsers support #page=N in the URL, but we'll return the file
        # and let the frontend handle the page navigation
        response = FileResponse(
            file_path,
            media_type="application/pdf",
            filename=filename,
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
            }
        )
        return response
    else:
        return FileResponse(
            file_path,
            media_type="application/pdf",
            filename=filename,
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
            }
        )


@router.get("")
async def list_documents():
    """List all available documents."""
    documents = []
    
    if DATA_DIR.exists():
        for file_path in DATA_DIR.glob("*.pdf"):
            documents.append({
                "filename": file_path.name,
                "size": file_path.stat().st_size,
            })
    
    return {"documents": documents}


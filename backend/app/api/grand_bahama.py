"""Grand Bahama institutional reference API.

Serves curated static JSON (ministry portfolio, MPs, local-government districts).
"""
import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter()
logger = logging.getLogger(__name__)

_API_DIR = Path(__file__).resolve().parent
_BACKEND_ROOT = _API_DIR.parent.parent
_REPO_ROOT = _BACKEND_ROOT.parent
_DATA_FILE = _REPO_ROOT / "data" / "grand_bahama" / "institutional.json"
_STATIC_FILE = _API_DIR / "static" / "grand_bahama" / "institutional.json"


def _load_dataset() -> dict[str, Any]:
    for path in (_DATA_FILE, _STATIC_FILE):
        if path.exists():
            try:
                with open(path) as f:
                    return json.load(f)
            except Exception as e:
                logger.warning("grand-bahama: failed to load %s: %s", path, e)
    raise HTTPException(status_code=404, detail="Grand Bahama institutional dataset not found")


@router.get("")
async def get_grand_bahama() -> dict[str, Any]:
    """Full Grand Bahama institutional reference payload."""
    return _load_dataset()


@router.get("/districts")
async def list_districts() -> list[dict[str, Any]]:
    """Grand Bahama local-government districts only."""
    data = _load_dataset()
    districts = data.get("districts")
    if not isinstance(districts, list):
        raise HTTPException(status_code=500, detail="Districts missing from dataset")
    return districts


@router.get("/mps")
async def list_mps() -> list[dict[str, Any]]:
    """Grand Bahama parliamentary delegation only."""
    data = _load_dataset()
    mps = data.get("mps")
    if not isinstance(mps, list):
        raise HTTPException(status_code=500, detail="MPs missing from dataset")
    return mps

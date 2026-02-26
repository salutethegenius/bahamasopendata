"""Hot Topics / featured reports API. Serves extracted report data (highlights, key_stats, chart_data)."""
import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter()
logger = logging.getLogger(__name__)

# Resolve paths relative to this module so they work from any cwd (e.g. deployment)
_API_DIR = Path(__file__).resolve().parent
_BACKEND_ROOT = _API_DIR.parent.parent
_REPO_ROOT = _BACKEND_ROOT.parent
_PROCESSED_DIR = _REPO_ROOT / "data" / "processed"
_STATIC_REPORTS = _API_DIR / "static" / "reports"


def _load_report(path: Path) -> dict[str, Any]:
    with open(path) as f:
        return json.load(f)


def _all_report_paths() -> list[Path]:
    """Collect *_report.json from processed dir and static dir (static as fallback)."""
    paths: list[Path] = []
    if _PROCESSED_DIR.exists():
        paths.extend(_PROCESSED_DIR.glob("*_report.json"))
    if _STATIC_REPORTS.exists():
        paths.extend(_STATIC_REPORTS.glob("*_report.json"))
    return paths


@router.get("/reports")
async def list_reports() -> list[dict[str, Any]]:
    """List available hot topic reports (slug, title, source, year for cards)."""
    seen: set[str] = set()
    reports: list[dict[str, Any]] = []
    try:
        paths = _all_report_paths()
        logger.debug("hot-topics: found %d report paths (processed=%s, static=%s)", len(paths), _PROCESSED_DIR, _STATIC_REPORTS)
        for path in paths:
            try:
                data = _load_report(path)
                slug = data.get("slug", path.stem.replace("_report", ""))
                if slug in seen:
                    continue
                seen.add(slug)
                summary = data.get("overview") or (data.get("highlights") or [None])[0] or ""
                reports.append({
                    "slug": slug,
                    "title": data.get("title", ""),
                    "source": data.get("source", ""),
                    "year": data.get("year", ""),
                    "summary": summary[:300] + ("..." if len(summary) > 300 else ""),
                    "stat_count": len(data.get("key_stats") or []),
                    "chart_count": len(data.get("charts") or []),
                    "highlight_count": len(data.get("highlights") or []),
                })
            except Exception as e:
                logger.warning("hot-topics: skip report %s: %s", path, e)
                continue
        reports.sort(key=lambda r: (r.get("year") or "", r.get("title") or ""), reverse=True)
        return reports
    except Exception as e:
        logger.exception("hot-topics: list_reports failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to load reports list")


@router.get("/reports/{slug}")
async def get_report(slug: str) -> dict[str, Any]:
    """Get full report by slug (highlights, key_stats, chart_data, pdf_filename)."""
    # Prefer processed (extracted) over static stub
    if _PROCESSED_DIR.exists():
        for path in _PROCESSED_DIR.glob("*_report.json"):
            try:
                data = _load_report(path)
                if data.get("slug") == slug:
                    return data
            except Exception:
                continue
    if _STATIC_REPORTS.exists():
        for path in _STATIC_REPORTS.glob("*_report.json"):
            try:
                data = _load_report(path)
                if data.get("slug") == slug:
                    return data
            except Exception:
                continue
    raise HTTPException(status_code=404, detail="Report not found")

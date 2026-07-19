"""Shared fiscal-year resolution for finance API routes."""

from __future__ import annotations

from typing import Optional

from fastapi import HTTPException


def fy_sort_key(fiscal_year: str | None) -> int:
    if not fiscal_year:
        return 0
    try:
        return int(str(fiscal_year).split("/")[0])
    except ValueError:
        return 0


def resolve_fiscal_year(
    fiscal_year: Optional[str],
    available_years: list[str],
    *,
    resource: str = "data",
) -> str | None:
    """Resolve a requested fiscal year against years that actually have data.

    - No available years → ``None`` (caller may return static fallbacks).
    - No request → latest available year.
    - Explicit request missing from available years → HTTP 404.
    """
    if not available_years:
        if fiscal_year:
            raise HTTPException(
                status_code=404,
                detail=f"No published {resource} for fiscal year {fiscal_year}",
            )
        return None

    if not fiscal_year:
        return available_years[-1]

    if fiscal_year not in available_years:
        raise HTTPException(
            status_code=404,
            detail=f"No published {resource} for fiscal year {fiscal_year}",
        )
    return fiscal_year

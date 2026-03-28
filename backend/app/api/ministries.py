"""Ministries API endpoints."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import BudgetItem, Document, Ministry as MinistryModel, MinistryAllocation
from app.services.finance_publisher import slugify_name

router = APIRouter()


class Ministry(BaseModel):
    """Ministry response model."""

    id: str
    name: str
    allocation: float
    previous_year_allocation: float
    change_percent: float
    sparkline: list[float]
    sector: str


class MinistryDetail(BaseModel):
    """Detailed ministry breakdown."""

    id: str
    name: str
    allocation: float
    salaries: float
    programs: float
    capital_projects: float
    grants: float
    line_items: list[dict]
    historical: list[dict]
    source_document: str
    source_page: int


FALLBACK_MINISTRIES = [
    Ministry(id="health", name="Ministry of Health & Wellness", allocation=355_119_623, previous_year_allocation=332_747_117, change_percent=6.7, sparkline=[288.4, 263.2, 332.7, 355.1], sector="Health"),
    Ministry(id="finance", name="Ministry of Finance", allocation=362_694_099, previous_year_allocation=346_639_187, change_percent=4.6, sparkline=[177.5, 178.8, 346.6, 362.7], sector="Finance"),
    Ministry(id="education", name="Ministry of Education & Technical Training", allocation=137_052_342, previous_year_allocation=123_252_555, change_percent=11.2, sparkline=[114.7, 91.4, 123.3, 137.1], sector="Education"),
    Ministry(id="police", name="Royal Bahamas Police Force", allocation=134_036_300, previous_year_allocation=126_644_406, change_percent=5.8, sparkline=[126.5, 100.9, 126.6, 134.0], sector="Security"),
    Ministry(id="tourism", name="Ministry of Tourism, Investments & Aviation", allocation=123_395_161, previous_year_allocation=131_376_411, change_percent=-6.1, sparkline=[140.5, 97.8, 131.4, 123.4], sector="Tourism"),
    Ministry(id="defence", name="Royal Bahamas Defence Force", allocation=77_530_944, previous_year_allocation=71_382_034, change_percent=8.6, sparkline=[69.0, 53.9, 71.4, 77.5], sector="Security"),
    Ministry(id="disaster", name="Ministry of Disaster Risk Management", allocation=60_518_380, previous_year_allocation=10_538_081, change_percent=474.3, sparkline=[11.9, 7.8, 10.5, 60.5], sector="Emergency"),
    Ministry(id="foreign-affairs", name="Ministry of Foreign Affairs", allocation=54_967_437, previous_year_allocation=50_682_286, change_percent=8.5, sparkline=[49.8, 39.7, 50.7, 55.0], sector="Government"),
    Ministry(id="social-services", name="Department of Social Services", allocation=53_074_475, previous_year_allocation=48_009_263, change_percent=10.5, sparkline=[47.7, 30.7, 48.0, 53.1], sector="Social Services"),
    Ministry(id="works", name="Ministry of Works & Family Island Affairs", allocation=48_213_665, previous_year_allocation=36_183_087, change_percent=33.2, sparkline=[49.9, 41.2, 36.2, 48.2], sector="Infrastructure"),
]


def _infer_sector(name: str | None) -> str:
    """Infer a product-friendly sector label when published data omits one."""
    lowered = (name or "").lower()
    if "health" in lowered:
        return "Health"
    if "education" in lowered:
        return "Education"
    if "finance" in lowered or "treasury" in lowered:
        return "Finance"
    if "tourism" in lowered or "aviation" in lowered:
        return "Tourism"
    if "works" in lowered or "infrastructure" in lowered or "transport" in lowered:
        return "Infrastructure"
    if "social" in lowered or "community" in lowered:
        return "Social Services"
    if "police" in lowered or "defence" in lowered or "security" in lowered:
        return "Security"
    if "disaster" in lowered or "emergency" in lowered:
        return "Emergency"
    return "Other"


def _fy_sort_key(fiscal_year: str | None) -> int:
    if not fiscal_year:
        return 0
    try:
        return int(str(fiscal_year).split("/")[0])
    except ValueError:
        return 0


async def _ministry_years(db: AsyncSession) -> list[str]:
    result = await db.execute(select(MinistryAllocation.fiscal_year))
    years = sorted({year for year in result.scalars().all() if year}, key=_fy_sort_key)
    return years


async def _latest_source_document(db: AsyncSession, fiscal_year: str) -> str:
    result = await db.execute(
        select(Document.filename)
        .where(
            Document.fiscal_year == fiscal_year,
            Document.document_type.in_(("budget_book", "budget_communication", "capital_estimates", "mid_year_statement")),
        )
        .order_by(Document.downloaded_at.desc())
    )
    filename = result.scalars().first()
    return filename or "Bahamas BudgetFINAL_2025-2026_.pdf"


@router.get("", response_model=list[Ministry])
async def get_ministries(db: AsyncSession = Depends(get_db)):
    """Get all ministries with allocations and YoY change."""
    years = await _ministry_years(db)
    if not years:
        return FALLBACK_MINISTRIES

    current_year = years[-1]
    previous_year = years[-2] if len(years) > 1 else None

    current_result = await db.execute(
        select(MinistryModel, MinistryAllocation)
        .join(MinistryAllocation, MinistryAllocation.ministry_id == MinistryModel.id)
        .where(MinistryAllocation.fiscal_year == current_year)
        .order_by(MinistryAllocation.total_allocation.desc())
    )
    current_rows = current_result.all()
    if not current_rows:
        return FALLBACK_MINISTRIES

    previous_result = await db.execute(
        select(MinistryAllocation.ministry_id, MinistryAllocation.total_allocation).where(
            MinistryAllocation.fiscal_year == previous_year
        )
    )
    previous_map = {ministry_id: float(total or 0.0) for ministry_id, total in previous_result.all()}

    historical_result = await db.execute(
        select(
            MinistryAllocation.ministry_id,
            MinistryAllocation.fiscal_year,
            MinistryAllocation.total_allocation,
        ).order_by(MinistryAllocation.fiscal_year.asc())
    )
    sparkline_map: dict[int, list[float]] = {}
    for ministry_id, fiscal_year, total in historical_result.all():
        sparkline_map.setdefault(ministry_id, []).append(round(float(total or 0.0) / 1_000_000, 1))

    ministries: list[Ministry] = []
    for ministry_row, allocation_row in current_rows:
        previous_allocation = previous_map.get(ministry_row.id, 0.0)
        change_percent = (
            ((allocation_row.total_allocation - previous_allocation) / previous_allocation) * 100
            if previous_allocation
            else 0.0
        )
        ministries.append(
            Ministry(
                id=slugify_name(ministry_row.name),
                name=ministry_row.name,
                allocation=float(allocation_row.total_allocation or 0.0),
                previous_year_allocation=float(previous_allocation),
                change_percent=round(change_percent, 1),
                sparkline=sparkline_map.get(ministry_row.id, []),
                sector=ministry_row.sector or _infer_sector(ministry_row.name),
            )
        )
    return ministries


@router.get("/{ministry_id}", response_model=MinistryDetail)
async def get_ministry_detail(ministry_id: str, db: AsyncSession = Depends(get_db)):
    """Get detailed breakdown for a specific ministry."""
    years = await _ministry_years(db)
    if not years:
        fallback = next((item for item in FALLBACK_MINISTRIES if item.id == ministry_id), None)
        if fallback:
            return MinistryDetail(
                id=fallback.id,
                name=fallback.name,
                allocation=fallback.allocation,
                salaries=0.0,
                programs=0.0,
                capital_projects=0.0,
                grants=0.0,
                line_items=[],
                historical=[{"year": years_index, "allocation": value * 1_000_000} for years_index, value in zip(["2022/23", "2023/24", "2024/25", "2025/26"], fallback.sparkline)],
                source_document="Bahamas BudgetFINAL_2025-2026_.pdf",
                source_page=71,
            )
        raise HTTPException(status_code=404, detail="Ministry not found")

    result = await db.execute(select(MinistryModel))
    ministries = result.scalars().all()
    ministry_row = next((row for row in ministries if slugify_name(row.name) == ministry_id or (row.code or "").lower() == ministry_id.lower()), None)
    if ministry_row is None:
        raise HTTPException(status_code=404, detail="Ministry not found")

    current_year = years[-1]
    allocation_result = await db.execute(
        select(MinistryAllocation).where(
            MinistryAllocation.ministry_id == ministry_row.id,
            MinistryAllocation.fiscal_year == current_year,
        )
    )
    allocation_row = allocation_result.scalars().first()
    if allocation_row is None:
        raise HTTPException(status_code=404, detail="Ministry allocation not found")

    historical_result = await db.execute(
        select(MinistryAllocation.fiscal_year, MinistryAllocation.total_allocation)
        .where(MinistryAllocation.ministry_id == ministry_row.id)
        .order_by(MinistryAllocation.fiscal_year.asc())
    )
    historical = [
        {"year": fiscal_year, "allocation": float(total or 0.0)}
        for fiscal_year, total in historical_result.all()
    ]

    line_items_result = await db.execute(
        select(BudgetItem)
        .where(
            BudgetItem.ministry_id == ministry_row.id,
            BudgetItem.fiscal_year == current_year,
        )
        .order_by(BudgetItem.amount.desc())
    )
    budget_items = line_items_result.scalars().all()
    line_items = [
        {"name": item.item_name, "amount": float(item.amount or 0.0)}
        for item in budget_items[:10]
    ]

    source_document = await _latest_source_document(db, current_year)
    return MinistryDetail(
        id=ministry_id,
        name=ministry_row.name,
        allocation=float(allocation_row.total_allocation or 0.0),
        salaries=float(allocation_row.salaries or 0.0),
        programs=float(allocation_row.programs or 0.0),
        capital_projects=float(allocation_row.capital_expenditure or 0.0),
        grants=float(allocation_row.grants or 0.0),
        line_items=line_items,
        historical=historical,
        source_document=source_document,
        source_page=allocation_row.source_page or 0,
    )


@router.get("/{ministry_id}/sparkline")
async def get_ministry_sparkline(ministry_id: str, years: int = 5, db: AsyncSession = Depends(get_db)):
    """Get sparkline data for a ministry's budget trend."""
    try:
        detail = await get_ministry_detail(ministry_id, db)
    except HTTPException:
        fallback = next((item for item in FALLBACK_MINISTRIES if item.id == ministry_id), None)
        if fallback is None:
            return {"ministry_id": ministry_id, "data": [], "years": []}
        return {
            "ministry_id": ministry_id,
            "data": fallback.sparkline[-years:],
            "years": ["2022/23", "2023/24", "2024/25", "2025/26"][-years:],
        }

    return {
        "ministry_id": ministry_id,
        "data": [round((item.get("allocation") or 0.0) / 1_000_000, 1) for item in detail.historical[-years:]],
        "years": [item.get("year") for item in detail.historical[-years:]],
    }

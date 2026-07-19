"""Revenue API endpoints."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.fiscal_year import fy_sort_key, resolve_fiscal_year
from app.db.database import get_db
from app.db.models import BudgetItem, Document, Revenue

router = APIRouter()


class RevenueSource(BaseModel):
    """Individual revenue source."""

    name: str
    amount: float
    percent_of_total: float
    change_yoy: float


class RevenueBreakdown(BaseModel):
    """Complete revenue breakdown."""

    fiscal_year: str
    total_revenue: float
    sources: list[RevenueSource]
    last_updated: date
    source_document: str


FALLBACK_BREAKDOWN = RevenueBreakdown(
    fiscal_year="2024/25",
    total_revenue=2_850_000_000,
    sources=[
        RevenueSource(name="Value Added Tax (VAT)", amount=1_100_000_000, percent_of_total=38.6, change_yoy=6.5),
        RevenueSource(name="Customs & Import Duties", amount=650_000_000, percent_of_total=22.8, change_yoy=4.2),
        RevenueSource(name="Tourism Taxes & Fees", amount=420_000_000, percent_of_total=14.7, change_yoy=12.5),
        RevenueSource(name="Business License Fees", amount=280_000_000, percent_of_total=9.8, change_yoy=3.8),
        RevenueSource(name="Property Tax", amount=150_000_000, percent_of_total=5.3, change_yoy=2.1),
        RevenueSource(name="Stamp Tax", amount=120_000_000, percent_of_total=4.2, change_yoy=1.5),
        RevenueSource(name="Other Revenue", amount=130_000_000, percent_of_total=4.6, change_yoy=5.0),
    ],
    last_updated=date.today(),
    source_document="Budget Book 2024-25.pdf",
)

FALLBACK_MONTHLY = {
    "fiscal_year": "2024/25",
    "monthly_data": [
        {"month": "Jul", "vat": 85_000_000, "customs": 52_000_000, "tourism": 35_000_000, "other": 48_000_000},
        {"month": "Aug", "vat": 90_000_000, "customs": 54_000_000, "tourism": 40_000_000, "other": 51_000_000},
        {"month": "Sep", "vat": 92_000_000, "customs": 55_000_000, "tourism": 42_000_000, "other": 56_000_000},
        {"month": "Oct", "vat": 95_000_000, "customs": 56_000_000, "tourism": 45_000_000, "other": 54_000_000},
        {"month": "Nov", "vat": 98_000_000, "customs": 58_000_000, "tourism": 48_000_000, "other": 56_000_000},
        {"month": "Dec", "vat": 105_000_000, "customs": 62_000_000, "tourism": 55_000_000, "other": 58_000_000},
    ],
    "source_document": "Revenue Report Q2 2024-25.pdf",
}

FALLBACK_HISTORICAL = {
    "years": [
        {"year": "2020/21", "total": 2_100_000_000, "vat": 780_000_000, "customs": 520_000_000, "tourism": 280_000_000},
        {"year": "2021/22", "total": 2_400_000_000, "vat": 900_000_000, "customs": 580_000_000, "tourism": 340_000_000},
        {"year": "2022/23", "total": 2_650_000_000, "vat": 1_000_000_000, "customs": 620_000_000, "tourism": 380_000_000},
        {"year": "2023/24", "total": 2_750_000_000, "vat": 1_050_000_000, "customs": 640_000_000, "tourism": 400_000_000},
        {"year": "2024/25", "total": 2_850_000_000, "vat": 1_100_000_000, "customs": 650_000_000, "tourism": 420_000_000},
    ]
}


async def _revenue_years(db: AsyncSession) -> list[str]:
    """Years with revenue source rows and/or budget-book revenue headlines."""
    years: set[str] = set()
    revenue_result = await db.execute(select(Revenue.fiscal_year))
    years.update(value for value in revenue_result.scalars().all() if value)
    headline_result = await db.execute(
        select(BudgetItem.fiscal_year).where(
            func.lower(BudgetItem.item_name).in_(
                ("total revenue", "recurrent revenue", "capital revenue")
            )
        )
    )
    years.update(value for value in headline_result.scalars().all() if value)
    return sorted(years, key=fy_sort_key)


async def _total_revenue_for_year(db: AsyncSession, fiscal_year: str) -> float:
    """Prefer the budget-book headline total; fall back to summing revenue source rows."""
    headline_result = await db.execute(
        select(BudgetItem.amount)
        .where(
            BudgetItem.fiscal_year == fiscal_year,
            func.lower(BudgetItem.item_name) == "total revenue",
        )
        .order_by(BudgetItem.amount.desc())
        .limit(1)
    )
    headline = headline_result.scalar()
    if headline is not None:
        return float(headline)

    total_result = await db.execute(
        select(func.coalesce(func.sum(Revenue.amount), 0.0)).where(Revenue.fiscal_year == fiscal_year)
    )
    return float(total_result.scalar() or 0.0)


async def _latest_source_document(db: AsyncSession, fiscal_year: str) -> str:
    result = await db.execute(
        select(Document.filename)
        .where(Document.fiscal_year == fiscal_year, Document.document_type == "revenue_estimates")
        .order_by(Document.downloaded_at.desc())
    )
    filename = result.scalars().first()
    return filename or FALLBACK_BREAKDOWN.source_document


@router.get("", response_model=RevenueBreakdown)
async def get_revenue_breakdown(
    fiscal_year: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get complete revenue breakdown by source."""
    years = await _revenue_years(db)
    target_year = resolve_fiscal_year(fiscal_year, years, resource="revenue data")
    if not target_year:
        return FALLBACK_BREAKDOWN

    total_revenue = await _total_revenue_for_year(db, target_year)
    if not total_revenue:
        if fiscal_year:
            raise HTTPException(
                status_code=404,
                detail=f"No published revenue data for fiscal year {fiscal_year}",
            )
        return FALLBACK_BREAKDOWN

    source_result = await db.execute(
        select(Revenue.source_name, func.coalesce(func.sum(Revenue.amount), 0.0))
        .where(Revenue.fiscal_year == target_year)
        .group_by(Revenue.source_name)
        .order_by(func.sum(Revenue.amount).desc())
    )
    previous_year = years[years.index(target_year) - 1] if years.index(target_year) > 0 else None
    previous_result = await db.execute(
        select(Revenue.source_name, func.coalesce(func.sum(Revenue.amount), 0.0))
        .where(Revenue.fiscal_year == previous_year)
        .group_by(Revenue.source_name)
    )
    previous_map = {name: float(total or 0.0) for name, total in previous_result.all()}

    sources = []
    for source_name, amount in source_result.all():
        amount_float = float(amount or 0.0)
        previous_amount = previous_map.get(source_name, 0.0)
        change_yoy = ((amount_float - previous_amount) / previous_amount * 100) if previous_amount else 0.0
        sources.append(
            RevenueSource(
                name=source_name,
                amount=amount_float,
                percent_of_total=round((amount_float / total_revenue) * 100, 1) if total_revenue else 0.0,
                change_yoy=round(change_yoy, 1),
            )
        )

    return RevenueBreakdown(
        fiscal_year=target_year,
        total_revenue=total_revenue,
        sources=sources,
        last_updated=date.today(),
        source_document=await _latest_source_document(db, target_year),
    )


@router.get("/monthly")
async def get_revenue_monthly(
    fiscal_year: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get monthly revenue collection data."""
    years = await _revenue_years(db)
    target_year = resolve_fiscal_year(fiscal_year, years, resource="monthly revenue data")
    if not target_year:
        return FALLBACK_MONTHLY

    result = await db.execute(
        select(Revenue.period, Revenue.source_name, func.coalesce(func.sum(Revenue.amount), 0.0))
        .where(
            Revenue.fiscal_year == target_year,
            Revenue.period.is_not(None),
            Revenue.period != "annual",
        )
        .group_by(Revenue.period, Revenue.source_name)
        .order_by(Revenue.period.asc())
    )
    rows = result.all()
    if not rows:
        # Monthly series is often absent from budget books; return empty for the year
        # rather than a different year's fallback mock data.
        return {
            "fiscal_year": target_year,
            "monthly_data": [],
            "source_document": await _latest_source_document(db, target_year),
        }

    monthly_map: dict[str, dict[str, float | str]] = {}
    for period, source_name, amount in rows:
        bucket = monthly_map.setdefault(period, {"month": period})
        key = source_name.lower()
        if "vat" in key:
            bucket["vat"] = float(amount or 0.0)
        elif "custom" in key:
            bucket["customs"] = float(amount or 0.0)
        elif "tour" in key:
            bucket["tourism"] = float(amount or 0.0)
        else:
            bucket["other"] = float(bucket.get("other", 0.0) or 0.0) + float(amount or 0.0)

    return {
        "fiscal_year": target_year,
        "monthly_data": list(monthly_map.values()),
        "source_document": await _latest_source_document(db, target_year),
    }


@router.get("/historical")
async def get_revenue_historical(years: int = 5, db: AsyncSession = Depends(get_db)):
    """Get historical revenue trends."""
    fiscal_years = await _revenue_years(db)
    if not fiscal_years:
        return FALLBACK_HISTORICAL

    historical_rows = []
    for fiscal_year in fiscal_years[-years:]:
        year_result = await db.execute(
            select(Revenue.source_name, func.coalesce(func.sum(Revenue.amount), 0.0))
            .where(Revenue.fiscal_year == fiscal_year)
            .group_by(Revenue.source_name)
        )
        grouped = {name.lower(): float(amount or 0.0) for name, amount in year_result.all()}
        historical_rows.append(
            {
                "year": fiscal_year,
                "total": sum(grouped.values()),
                "vat": sum(amount for name, amount in grouped.items() if "vat" in name),
                "customs": sum(amount for name, amount in grouped.items() if "custom" in name),
                "tourism": sum(amount for name, amount in grouped.items() if "tour" in name),
            }
        )

    return {"years": historical_rows or FALLBACK_HISTORICAL["years"]}

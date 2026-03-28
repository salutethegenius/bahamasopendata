"""Budget API endpoints."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import BudgetItem, Debt, Document, Ministry, MinistryAllocation, Revenue

router = APIRouter()


class BudgetSummary(BaseModel):
    """Budget summary response model."""

    fiscal_year: str
    total_revenue: float
    total_expenditure: float
    recurrent_expenditure: float
    capital_expenditure: float
    deficit_surplus: float
    national_debt: float
    debt_to_gdp_ratio: Optional[float] = None
    gdp: Optional[float] = None
    last_updated: date
    source_document: str
    source_page: Optional[int] = None


FALLBACK_SUMMARY = BudgetSummary(
    fiscal_year="2025/26",
    total_revenue=3_896_324_553,
    total_expenditure=3_820_844_050,
    recurrent_expenditure=3_444_518_797,
    capital_expenditure=376_325_253,
    deficit_surplus=75_480_503,
    national_debt=11_386_500_000,
    debt_to_gdp_ratio=68.9,
    gdp=16_525_700_000,
    last_updated=date(2025, 5, 28),
    source_document="Bahamas BudgetFINAL_2025-2026_.pdf",
    source_page=34,
)

FALLBACK_HISTORICAL = [
    {"year": "2020/21", "revenue": 1_908_600_000, "expenditure": 3_243_600_000, "debt": 9_934_800_000, "debt_gdp": 88.7},
    {"year": "2021/22", "revenue": 2_605_300_000, "expenditure": 3_327_900_000, "debt": 10_792_400_000, "debt_gdp": 83.2},
    {"year": "2022/23", "revenue": 2_854_200_000, "expenditure": 3_390_000_000, "debt": 11_259_500_000, "debt_gdp": 77.2},
    {"year": "2023/24", "revenue": 3_069_100_000, "expenditure": 3_263_100_000, "debt": 11_313_800_000, "debt_gdp": 72.7},
    {"year": "2024/25", "revenue": 3_537_000_000, "expenditure": 3_613_100_000, "debt": 11_461_000_000, "debt_gdp": 71.4},
    {"year": "2025/26", "revenue": 3_887_100_000, "expenditure": 3_820_800_000, "debt": 11_386_500_000, "debt_gdp": 68.9},
]

FALLBACK_SECTORS = [
    {"name": "Education", "amount": 353_413_898, "color": "#00CED1"},
    {"name": "Health", "amount": 477_596_494, "color": "#FCD116"},
    {"name": "National Security", "amount": 231_980_608, "color": "#3b82f6"},
    {"name": "Public Debt Service", "amount": 689_545_978, "color": "#ef4444"},
    {"name": "Social Services", "amount": 72_243_034, "color": "#10b981"},
    {"name": "Works & Infrastructure", "amount": 69_262_014, "color": "#f59e0b"},
    {"name": "Tourism", "amount": 123_395_161, "color": "#8b5cf6"},
    {"name": "Other", "amount": 1_427_081_610, "color": "#6b7280"},
]


def _infer_sector(name: str | None) -> str:
    """Infer a sector label from ministry names when no explicit sector exists."""
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
        return "National Security"
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


async def _get_finance_years(db: AsyncSession) -> list[str]:
    years: set[str] = set()
    for model in (Revenue, MinistryAllocation, Debt):
        result = await db.execute(select(model.fiscal_year))
        years.update(value for value in result.scalars().all() if value)
    return sorted(years, key=_fy_sort_key)


async def _sum_revenue_for_year(db: AsyncSession, fiscal_year: str) -> float:
    result = await db.execute(
        select(func.coalesce(func.sum(Revenue.amount), 0.0)).where(Revenue.fiscal_year == fiscal_year)
    )
    return float(result.scalar() or 0.0)


async def _sum_expenditure_for_year(db: AsyncSession, fiscal_year: str) -> float:
    result = await db.execute(
        select(func.coalesce(func.sum(MinistryAllocation.total_allocation), 0.0)).where(
            MinistryAllocation.fiscal_year == fiscal_year
        )
    )
    return float(result.scalar() or 0.0)


async def _sum_budget_items_for_year(db: AsyncSession, fiscal_year: str, categories: set[str]) -> float:
    result = await db.execute(
        select(func.coalesce(func.sum(BudgetItem.amount), 0.0)).where(
            BudgetItem.fiscal_year == fiscal_year,
            BudgetItem.category.in_(list(categories)),
        )
    )
    return float(result.scalar() or 0.0)


async def _latest_document_name(db: AsyncSession, fiscal_year: str, document_types: tuple[str, ...] | None = None) -> str | None:
    statement = select(Document).where(Document.fiscal_year == fiscal_year)
    if document_types:
        statement = statement.where(Document.document_type.in_(document_types))
    statement = statement.order_by(Document.downloaded_at.desc())
    result = await db.execute(statement)
    document = result.scalars().first()
    return document.filename if document else None


@router.get("/summary", response_model=BudgetSummary)
async def get_budget_summary(
    fiscal_year: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get the budget summary for a fiscal year."""
    years = await _get_finance_years(db)
    target_year = fiscal_year or (years[-1] if years else None)
    if not target_year:
        return FALLBACK_SUMMARY

    total_revenue = await _sum_revenue_for_year(db, target_year)
    total_expenditure = await _sum_expenditure_for_year(db, target_year)
    debt_result = await db.execute(
        select(Debt).where(Debt.fiscal_year == target_year).order_by(Debt.created_at.desc())
    )
    debt_row = debt_result.scalars().first()

    if not total_revenue and not total_expenditure and debt_row is None:
        return FALLBACK_SUMMARY if target_year == FALLBACK_SUMMARY.fiscal_year else FALLBACK_SUMMARY

    recurrent_expenditure = await _sum_budget_items_for_year(
        db,
        target_year,
        {"recurrent_expenditure", "salary", "salaries", "program", "programs", "grant", "grants"},
    )
    capital_expenditure = await _sum_budget_items_for_year(
        db,
        target_year,
        {"capital", "capital_expenditure", "capital_project", "capital_projects"},
    )

    if not recurrent_expenditure and not capital_expenditure:
        recurrent_result = await db.execute(
            select(func.coalesce(func.sum(MinistryAllocation.recurrent_expenditure), 0.0)).where(
                MinistryAllocation.fiscal_year == target_year
            )
        )
        capital_result = await db.execute(
            select(func.coalesce(func.sum(MinistryAllocation.capital_expenditure), 0.0)).where(
                MinistryAllocation.fiscal_year == target_year
            )
        )
        recurrent_expenditure = float(recurrent_result.scalar() or 0.0)
        capital_expenditure = float(capital_result.scalar() or 0.0)

    summary_source = await _latest_document_name(
        db,
        target_year,
        ("budget_book", "budget_communication", "capital_estimates", "mid_year_statement"),
    ) or FALLBACK_SUMMARY.source_document
    debt_to_gdp_ratio = debt_row.debt_to_gdp_ratio if debt_row else FALLBACK_SUMMARY.debt_to_gdp_ratio
    gdp = debt_row.gdp if debt_row else FALLBACK_SUMMARY.gdp
    national_debt = debt_row.total_debt if debt_row else FALLBACK_SUMMARY.national_debt

    return BudgetSummary(
        fiscal_year=target_year,
        total_revenue=total_revenue or FALLBACK_SUMMARY.total_revenue,
        total_expenditure=total_expenditure or FALLBACK_SUMMARY.total_expenditure,
        recurrent_expenditure=recurrent_expenditure or FALLBACK_SUMMARY.recurrent_expenditure,
        capital_expenditure=capital_expenditure or FALLBACK_SUMMARY.capital_expenditure,
        deficit_surplus=(total_revenue or FALLBACK_SUMMARY.total_revenue)
        - (total_expenditure or FALLBACK_SUMMARY.total_expenditure),
        national_debt=national_debt,
        debt_to_gdp_ratio=debt_to_gdp_ratio,
        gdp=gdp,
        last_updated=date.today(),
        source_document=summary_source,
        source_page=None,
    )


@router.get("/priorities")
async def get_budget_priorities():
    """Get the four budget priorities/pillars."""
    return {
        "fiscal_year": "2025/26",
        "priorities": [
            {"name": "Security", "description": "National security and personal safety", "icon": "shield"},
            {"name": "Opportunity", "description": "Growing the economy and investing in our people", "icon": "trending-up"},
            {"name": "Affordability", "description": "Combating inflation and lowering prices", "icon": "dollar-sign"},
            {"name": "Reform", "description": "Fiscal discipline and modernizing government services", "icon": "settings"},
        ],
        "source_document": "Budget_Communication_25_26_final_1.pdf",
        "source_page": 3,
    }


@router.get("/historical")
async def get_historical_budgets(years: int = 10, db: AsyncSession = Depends(get_db)):
    """Get historical budget data for trend analysis."""
    fiscal_years = await _get_finance_years(db)
    if not fiscal_years:
        return {
            "years": FALLBACK_HISTORICAL[-years:],
            "source_document": FALLBACK_SUMMARY.source_document,
            "source_page": 34,
        }

    historical_rows: list[dict[str, float | str | None]] = []
    for fiscal_year in fiscal_years[-years:]:
        debt_result = await db.execute(
            select(Debt).where(Debt.fiscal_year == fiscal_year).order_by(Debt.created_at.desc())
        )
        debt_row = debt_result.scalars().first()
        historical_rows.append(
            {
                "year": fiscal_year,
                "revenue": await _sum_revenue_for_year(db, fiscal_year),
                "expenditure": await _sum_expenditure_for_year(db, fiscal_year),
                "debt": debt_row.total_debt if debt_row else 0.0,
                "debt_gdp": debt_row.debt_to_gdp_ratio if debt_row else None,
            }
        )

    return {
        "years": historical_rows or FALLBACK_HISTORICAL[-years:],
        "source_document": await _latest_document_name(
            db,
            fiscal_years[-1],
            ("budget_book", "budget_communication", "capital_estimates", "mid_year_statement"),
        ) or FALLBACK_SUMMARY.source_document,
        "source_page": None,
    }


@router.get("/sector-breakdown")
async def get_sector_breakdown(db: AsyncSession = Depends(get_db)):
    """Get expenditure breakdown by major sectors."""
    fiscal_years = await _get_finance_years(db)
    if not fiscal_years:
        return {
            "fiscal_year": FALLBACK_SUMMARY.fiscal_year,
            "sectors": FALLBACK_SECTORS,
            "total": FALLBACK_SUMMARY.recurrent_expenditure,
            "source_document": FALLBACK_SUMMARY.source_document,
            "source_page": 71,
        }

    target_year = fiscal_years[-1]
    result = await db.execute(
        select(
            Ministry.name,
            Ministry.sector,
            MinistryAllocation.total_allocation,
        )
        .join(MinistryAllocation, MinistryAllocation.ministry_id == Ministry.id)
        .where(MinistryAllocation.fiscal_year == target_year)
    )
    allocation_rows = result.all()
    if not allocation_rows:
        return {
            "fiscal_year": FALLBACK_SUMMARY.fiscal_year,
            "sectors": FALLBACK_SECTORS,
            "total": FALLBACK_SUMMARY.recurrent_expenditure,
            "source_document": FALLBACK_SUMMARY.source_document,
            "source_page": 71,
        }

    colors = ["#00CED1", "#FCD116", "#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6", "#6b7280"]
    sector_totals: dict[str, float] = {}
    for ministry_name, sector, total_allocation in allocation_rows:
        resolved_sector = sector or _infer_sector(ministry_name)
        sector_totals[resolved_sector] = sector_totals.get(resolved_sector, 0.0) + float(total_allocation or 0.0)

    sectors = [
        {
            "name": sector_name,
            "amount": amount,
            "color": colors[index % len(colors)],
        }
        for index, (sector_name, amount) in enumerate(
            sorted(sector_totals.items(), key=lambda item: item[1], reverse=True)
        )
    ]
    total = sum(item["amount"] for item in sectors)
    return {
        "fiscal_year": target_year,
        "sectors": sectors,
        "total": total,
        "source_document": await _latest_document_name(
            db,
            target_year,
            ("budget_book", "budget_communication", "capital_estimates", "mid_year_statement"),
        ) or FALLBACK_SUMMARY.source_document,
        "source_page": None,
    }

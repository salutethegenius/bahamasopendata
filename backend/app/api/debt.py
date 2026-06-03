"""Debt and Loans API endpoints."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import Creditor as CreditorModel, Debt, Document

router = APIRouter()


class DebtSummary(BaseModel):
    """National debt summary."""

    total_debt: float
    domestic_debt: float
    external_debt: float
    debt_to_gdp_ratio: float
    annual_interest_cost: float
    change_yoy: float
    last_updated: date
    source_document: str


class Creditor(BaseModel):
    """Major creditor information."""

    name: str
    category: str
    amount: float
    percent_of_total: float


class RepaymentSchedule(BaseModel):
    """Debt repayment schedule item."""

    year: str
    principal: float
    interest: float
    total: float


FALLBACK_SUMMARY = DebtSummary(
    total_debt=11_500_000_000,
    domestic_debt=6_200_000_000,
    external_debt=5_300_000_000,
    debt_to_gdp_ratio=82.5,
    annual_interest_cost=580_000_000,
    change_yoy=1.8,
    last_updated=date.today(),
    source_document="Debt Report 2024-25.pdf",
)

FALLBACK_CREDITORS = [
    Creditor(name="Domestic Government Bonds", category="domestic", amount=4_500_000_000, percent_of_total=39.1),
    Creditor(name="Domestic Treasury Bills", category="domestic", amount=1_700_000_000, percent_of_total=14.8),
    Creditor(name="Inter-American Development Bank", category="multilateral", amount=1_800_000_000, percent_of_total=15.7),
    Creditor(name="International Monetary Fund", category="multilateral", amount=400_000_000, percent_of_total=3.5),
    Creditor(name="Caribbean Development Bank", category="multilateral", amount=350_000_000, percent_of_total=3.0),
    Creditor(name="People's Republic of China", category="bilateral", amount=580_000_000, percent_of_total=5.0),
    Creditor(name="Commercial Banks", category="commercial", amount=1_200_000_000, percent_of_total=10.4),
    Creditor(name="Other External", category="commercial", amount=970_000_000, percent_of_total=8.5),
]

FALLBACK_REPAYMENT = [
    RepaymentSchedule(year="2024/25", principal=450_000_000, interest=580_000_000, total=1_030_000_000),
    RepaymentSchedule(year="2025/26", principal=520_000_000, interest=560_000_000, total=1_080_000_000),
    RepaymentSchedule(year="2026/27", principal=580_000_000, interest=540_000_000, total=1_120_000_000),
    RepaymentSchedule(year="2027/28", principal=650_000_000, interest=510_000_000, total=1_160_000_000),
    RepaymentSchedule(year="2028/29", principal=720_000_000, interest=480_000_000, total=1_200_000_000),
]

FALLBACK_HISTORICAL = {
    "years": [
        {"year": "2015/16", "total": 6_800_000_000, "domestic": 3_800_000_000, "external": 3_000_000_000, "gdp_ratio": 62.5},
        {"year": "2016/17", "total": 7_200_000_000, "domestic": 4_000_000_000, "external": 3_200_000_000, "gdp_ratio": 65.0},
        {"year": "2017/18", "total": 7_600_000_000, "domestic": 4_200_000_000, "external": 3_400_000_000, "gdp_ratio": 67.5},
        {"year": "2018/19", "total": 8_100_000_000, "domestic": 4_500_000_000, "external": 3_600_000_000, "gdp_ratio": 70.0},
        {"year": "2019/20", "total": 8_500_000_000, "domestic": 4_700_000_000, "external": 3_800_000_000, "gdp_ratio": 72.0},
        {"year": "2020/21", "total": 10_200_000_000, "domestic": 5_500_000_000, "external": 4_700_000_000, "gdp_ratio": 85.0},
        {"year": "2021/22", "total": 10_800_000_000, "domestic": 5_800_000_000, "external": 5_000_000_000, "gdp_ratio": 84.0},
        {"year": "2022/23", "total": 11_100_000_000, "domestic": 6_000_000_000, "external": 5_100_000_000, "gdp_ratio": 83.0},
        {"year": "2023/24", "total": 11_300_000_000, "domestic": 6_100_000_000, "external": 5_200_000_000, "gdp_ratio": 82.8},
        {"year": "2024/25", "total": 11_500_000_000, "domestic": 6_200_000_000, "external": 5_300_000_000, "gdp_ratio": 82.5},
    ]
}


def _fy_sort_key(fiscal_year: str | None) -> int:
    if not fiscal_year:
        return 0
    try:
        return int(str(fiscal_year).split("/")[0])
    except ValueError:
        return 0


async def _debt_years(db: AsyncSession) -> list[str]:
    result = await db.execute(select(Debt.fiscal_year))
    return sorted({value for value in result.scalars().all() if value}, key=_fy_sort_key)


async def _latest_document_name(db: AsyncSession, fiscal_year: str) -> str:
    result = await db.execute(
        select(Document.filename)
        .where(Document.fiscal_year == fiscal_year, Document.document_type == "debt_report")
        .order_by(Document.downloaded_at.desc())
    )
    filename = result.scalars().first()
    return filename or FALLBACK_SUMMARY.source_document


@router.get("", response_model=DebtSummary)
async def get_debt_summary(
    fiscal_year: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get national debt summary."""
    years = await _debt_years(db)
    if not years:
        return FALLBACK_SUMMARY

    current_year = fiscal_year if fiscal_year in years else years[-1]
    current_index = years.index(current_year)
    previous_year = years[current_index - 1] if current_index > 0 else None
    current_result = await db.execute(
        select(Debt).where(Debt.fiscal_year == current_year).order_by(Debt.created_at.desc())
    )
    current_row = current_result.scalars().first()
    if current_row is None:
        return FALLBACK_SUMMARY

    previous_result = await db.execute(
        select(Debt).where(Debt.fiscal_year == previous_year).order_by(Debt.created_at.desc())
    )
    previous_row = previous_result.scalars().first()
    previous_total = float(previous_row.total_debt) if previous_row else 0.0
    change_yoy = ((float(current_row.total_debt) - previous_total) / previous_total * 100) if previous_total else 0.0

    return DebtSummary(
        total_debt=float(current_row.total_debt or 0.0),
        domestic_debt=float(current_row.domestic_debt or 0.0),
        external_debt=float(current_row.external_debt or 0.0),
        debt_to_gdp_ratio=float(current_row.debt_to_gdp_ratio or 0.0),
        annual_interest_cost=float(current_row.annual_interest or 0.0),
        change_yoy=round(change_yoy, 1),
        last_updated=date.today(),
        source_document=await _latest_document_name(db, current_year),
    )


@router.get("/overview", response_model=DebtSummary)
async def get_debt_overview(
    fiscal_year: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Alias for the debt summary endpoint used by overview-style clients."""
    return await get_debt_summary(fiscal_year=fiscal_year, db=db)


@router.get("/creditors", response_model=list[Creditor])
async def get_creditors(
    fiscal_year: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get breakdown of major creditors."""
    years = await _debt_years(db)
    if not years:
        return FALLBACK_CREDITORS

    current_year = fiscal_year if fiscal_year in years else years[-1]
    debt_result = await db.execute(select(Debt).where(Debt.fiscal_year == current_year).order_by(Debt.created_at.desc()))
    debt_row = debt_result.scalars().first()
    total_debt = float(debt_row.total_debt or 0.0) if debt_row else 0.0

    result = await db.execute(
        select(CreditorModel)
        .where(CreditorModel.fiscal_year == current_year)
        .order_by(CreditorModel.amount_owed.desc())
    )
    creditors = result.scalars().all()
    if not creditors:
        return FALLBACK_CREDITORS

    return [
        Creditor(
            name=creditor.name,
            category=creditor.category or "other",
            amount=float(creditor.amount_owed or 0.0),
            percent_of_total=round((float(creditor.amount_owed or 0.0) / total_debt) * 100, 1) if total_debt else 0.0,
        )
        for creditor in creditors
    ]


@router.get("/repayment-schedule", response_model=list[RepaymentSchedule])
async def get_repayment_schedule():
    """Get debt repayment schedule for next 5 years."""
    return FALLBACK_REPAYMENT


@router.get("/historical")
async def get_debt_historical(years: int = 10, db: AsyncSession = Depends(get_db)):
    """Get historical debt levels."""
    fiscal_years = await _debt_years(db)
    if not fiscal_years:
        return FALLBACK_HISTORICAL

    result = await db.execute(select(Debt).order_by(Debt.fiscal_year.asc(), Debt.created_at.asc()))
    seen_years: dict[str, Debt] = {}
    for row in result.scalars().all():
        seen_years[row.fiscal_year] = row

    return {
        "years": [
            {
                "year": fiscal_year,
                "total": float(row.total_debt or 0.0),
                "domestic": float(row.domestic_debt or 0.0),
                "external": float(row.external_debt or 0.0),
                "gdp_ratio": float(row.debt_to_gdp_ratio or 0.0),
            }
            for fiscal_year, row in list(seen_years.items())[-years:]
        ]
    }

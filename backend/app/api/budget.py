"""Budget API endpoints."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import date

router = APIRouter()


class BudgetSummary(BaseModel):
    """Budget summary response model."""
    fiscal_year: str
    total_revenue: float
    total_expenditure: float
    deficit_surplus: float
    national_debt: float
    debt_to_gdp_ratio: Optional[float] = None
    revenue_change_yoy: Optional[float] = None
    expenditure_change_yoy: Optional[float] = None
    last_updated: date
    source_document: str
    source_page: Optional[int] = None


class MonthlyBreakdown(BaseModel):
    """Monthly revenue/expenditure breakdown."""
    month: str
    revenue: float
    expenditure: float


@router.get("/summary", response_model=BudgetSummary)
async def get_budget_summary(fiscal_year: Optional[str] = None):
    """
    Get the budget summary for a fiscal year.
    
    Returns total revenue, expenditure, deficit/surplus, and debt levels.
    """
    # TODO: Fetch from database
    return BudgetSummary(
        fiscal_year="2024/25",
        total_revenue=2_850_000_000,
        total_expenditure=3_200_000_000,
        deficit_surplus=-350_000_000,
        national_debt=11_500_000_000,
        debt_to_gdp_ratio=82.5,
        revenue_change_yoy=5.2,
        expenditure_change_yoy=3.8,
        last_updated=date.today(),
        source_document="Budget Communication 2024-25.pdf",
        source_page=12,
    )


@router.get("/monthly")
async def get_monthly_breakdown(fiscal_year: Optional[str] = None):
    """Get month-by-month revenue and expenditure breakdown."""
    # TODO: Fetch from database
    return {
        "fiscal_year": "2024/25",
        "months": [
            {"month": "Jul", "revenue": 220_000_000, "expenditure": 260_000_000},
            {"month": "Aug", "revenue": 235_000_000, "expenditure": 265_000_000},
            {"month": "Sep", "revenue": 245_000_000, "expenditure": 270_000_000},
            {"month": "Oct", "revenue": 250_000_000, "expenditure": 268_000_000},
            {"month": "Nov", "revenue": 260_000_000, "expenditure": 275_000_000},
            {"month": "Dec", "revenue": 280_000_000, "expenditure": 285_000_000},
        ],
        "source_document": "Mid-Year Budget Statement 2024-25.pdf",
    }


@router.get("/historical")
async def get_historical_budgets(years: int = 10):
    """Get historical budget data for trend analysis."""
    # TODO: Fetch from database
    return {
        "years": [
            {"year": "2015/16", "revenue": 2_100_000_000, "expenditure": 2_350_000_000, "debt": 6_800_000_000},
            {"year": "2016/17", "revenue": 2_200_000_000, "expenditure": 2_450_000_000, "debt": 7_200_000_000},
            {"year": "2017/18", "revenue": 2_350_000_000, "expenditure": 2_550_000_000, "debt": 7_600_000_000},
            {"year": "2018/19", "revenue": 2_450_000_000, "expenditure": 2_650_000_000, "debt": 8_100_000_000},
            {"year": "2019/20", "revenue": 2_550_000_000, "expenditure": 2_800_000_000, "debt": 8_500_000_000},
            {"year": "2020/21", "revenue": 2_100_000_000, "expenditure": 3_200_000_000, "debt": 10_200_000_000},
            {"year": "2021/22", "revenue": 2_400_000_000, "expenditure": 3_100_000_000, "debt": 10_800_000_000},
            {"year": "2022/23", "revenue": 2_650_000_000, "expenditure": 3_050_000_000, "debt": 11_100_000_000},
            {"year": "2023/24", "revenue": 2_750_000_000, "expenditure": 3_100_000_000, "debt": 11_300_000_000},
            {"year": "2024/25", "revenue": 2_850_000_000, "expenditure": 3_200_000_000, "debt": 11_500_000_000},
        ]
    }


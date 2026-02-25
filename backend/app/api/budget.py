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
    recurrent_expenditure: float
    capital_expenditure: float
    deficit_surplus: float
    national_debt: float
    debt_to_gdp_ratio: Optional[float] = None
    gdp: Optional[float] = None
    last_updated: date
    source_document: str
    source_page: Optional[int] = None


class MonthlyBreakdown(BaseModel):
    """Monthly revenue/expenditure breakdown."""
    month: str
    revenue: float
    expenditure: float


class BudgetPriority(BaseModel):
    """Budget priority/pillar."""
    name: str
    description: str
    icon: str


@router.get("/summary", response_model=BudgetSummary)
async def get_budget_summary(fiscal_year: Optional[str] = None):
    """
    Get the budget summary for a fiscal year.
    
    Returns total revenue, expenditure, deficit/surplus, and debt levels.
    Data sourced from Bahamas Budget 2025/26.
    """
    # Real data from Budget Book 2025/26
    return BudgetSummary(
        fiscal_year="2025/26",
        total_revenue=3_896_324_553,  # Page 66
        total_expenditure=3_820_844_050,  # Recurrent + Capital
        recurrent_expenditure=3_444_518_797,  # Page 227
        capital_expenditure=376_325_253,  # Page 246
        deficit_surplus=75_480_503,  # Surplus! First balanced budget
        national_debt=11_386_500_000,  # End of FY2025/26 projection
        debt_to_gdp_ratio=68.9,  # Page 34 - Fiscal Summary
        gdp=16_525_700_000,  # GDP current prices 2025/26
        last_updated=date(2025, 5, 28),  # Budget presentation date
        source_document="Bahamas BudgetFINAL_2025-2026_.pdf",
        source_page=34,
    )


@router.get("/priorities")
async def get_budget_priorities():
    """Get the four budget priorities/pillars."""
    return {
        "fiscal_year": "2025/26",
        "priorities": [
            {
                "name": "Security",
                "description": "National security and personal safety",
                "icon": "shield",
            },
            {
                "name": "Opportunity",
                "description": "Growing the economy and investing in our people",
                "icon": "trending-up",
            },
            {
                "name": "Affordability",
                "description": "Combating inflation and lowering prices",
                "icon": "dollar-sign",
            },
            {
                "name": "Reform",
                "description": "Fiscal discipline and modernizing government services",
                "icon": "settings",
            },
        ],
        "source_document": "Budget_Communication_25_26_final_1.pdf",
        "source_page": 3,
    }


@router.get("/historical")
async def get_historical_budgets(years: int = 10):
    """Get historical budget data for trend analysis from Fiscal Summary."""
    # Real data from Fiscal Summary table (Page 34)
    return {
        "years": [
            {"year": "2020/21", "revenue": 1_908_600_000, "expenditure": 3_243_600_000, "debt": 9_934_800_000, "debt_gdp": 88.7},
            {"year": "2021/22", "revenue": 2_605_300_000, "expenditure": 3_327_900_000, "debt": 10_792_400_000, "debt_gdp": 83.2},
            {"year": "2022/23", "revenue": 2_854_200_000, "expenditure": 3_390_000_000, "debt": 11_259_500_000, "debt_gdp": 77.2},
            {"year": "2023/24", "revenue": 3_069_100_000, "expenditure": 3_263_100_000, "debt": 11_313_800_000, "debt_gdp": 72.7},
            {"year": "2024/25", "revenue": 3_537_000_000, "expenditure": 3_613_100_000, "debt": 11_461_000_000, "debt_gdp": 71.4},
            {"year": "2025/26", "revenue": 3_887_100_000, "expenditure": 3_820_800_000, "debt": 11_386_500_000, "debt_gdp": 68.9},
        ],
        "source_document": "Bahamas BudgetFINAL_2025-2026_.pdf",
        "source_page": 34,
    }


@router.get("/sector-breakdown")
async def get_sector_breakdown():
    """Get expenditure breakdown by major sectors."""
    return {
        "fiscal_year": "2025/26",
        "sectors": [
            {"name": "Education", "amount": 353_413_898, "color": "#00CED1"},  # MOE + Dept Education + Technical
            {"name": "Health", "amount": 477_596_494, "color": "#FCD116"},  # MOH + Environmental Health + Public Health
            {"name": "National Security", "amount": 231_980_608, "color": "#3b82f6"},  # Police + Defence + MON Security
            {"name": "Public Debt Service", "amount": 689_545_978, "color": "#ef4444"},  # Interest & Charges
            {"name": "Social Services", "amount": 72_243_034, "color": "#10b981"},  # Social Services Dept + Ministry
            {"name": "Works & Infrastructure", "amount": 69_262_014, "color": "#f59e0b"},  # Ministry + Dept Works
            {"name": "Tourism", "amount": 123_395_161, "color": "#8b5cf6"},
            {"name": "Other", "amount": 1_427_081_610, "color": "#6b7280"},
        ],
        "total": 3_444_518_797,
        "source_document": "Bahamas BudgetFINAL_2025-2026_.pdf",
        "source_page": 71,
    }


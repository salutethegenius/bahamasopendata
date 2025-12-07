"""Debt and Loans API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from datetime import date

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
    category: str  # "domestic", "bilateral", "multilateral", "commercial"
    amount: float
    percent_of_total: float


class RepaymentSchedule(BaseModel):
    """Debt repayment schedule item."""
    year: str
    principal: float
    interest: float
    total: float


@router.get("", response_model=DebtSummary)
async def get_debt_summary():
    """Get national debt summary."""
    # TODO: Fetch from database
    return DebtSummary(
        total_debt=11_500_000_000,
        domestic_debt=6_200_000_000,
        external_debt=5_300_000_000,
        debt_to_gdp_ratio=82.5,
        annual_interest_cost=580_000_000,
        change_yoy=1.8,
        last_updated=date.today(),
        source_document="Debt Report 2024-25.pdf",
    )


@router.get("/creditors", response_model=list[Creditor])
async def get_creditors():
    """Get breakdown of major creditors."""
    # TODO: Fetch from database
    return [
        Creditor(
            name="Domestic Government Bonds",
            category="domestic",
            amount=4_500_000_000,
            percent_of_total=39.1,
        ),
        Creditor(
            name="Domestic Treasury Bills",
            category="domestic",
            amount=1_700_000_000,
            percent_of_total=14.8,
        ),
        Creditor(
            name="Inter-American Development Bank",
            category="multilateral",
            amount=1_800_000_000,
            percent_of_total=15.7,
        ),
        Creditor(
            name="International Monetary Fund",
            category="multilateral",
            amount=400_000_000,
            percent_of_total=3.5,
        ),
        Creditor(
            name="Caribbean Development Bank",
            category="multilateral",
            amount=350_000_000,
            percent_of_total=3.0,
        ),
        Creditor(
            name="People's Republic of China",
            category="bilateral",
            amount=580_000_000,
            percent_of_total=5.0,
        ),
        Creditor(
            name="Commercial Banks",
            category="commercial",
            amount=1_200_000_000,
            percent_of_total=10.4,
        ),
        Creditor(
            name="Other External",
            category="commercial",
            amount=970_000_000,
            percent_of_total=8.5,
        ),
    ]


@router.get("/repayment-schedule", response_model=list[RepaymentSchedule])
async def get_repayment_schedule():
    """Get debt repayment schedule for next 5 years."""
    # TODO: Fetch from database
    return [
        RepaymentSchedule(year="2024/25", principal=450_000_000, interest=580_000_000, total=1_030_000_000),
        RepaymentSchedule(year="2025/26", principal=520_000_000, interest=560_000_000, total=1_080_000_000),
        RepaymentSchedule(year="2026/27", principal=580_000_000, interest=540_000_000, total=1_120_000_000),
        RepaymentSchedule(year="2027/28", principal=650_000_000, interest=510_000_000, total=1_160_000_000),
        RepaymentSchedule(year="2028/29", principal=720_000_000, interest=480_000_000, total=1_200_000_000),
    ]


@router.get("/historical")
async def get_debt_historical(years: int = 10):
    """Get historical debt levels."""
    # TODO: Fetch from database
    return {
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


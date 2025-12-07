"""Revenue API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from datetime import date

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


@router.get("", response_model=RevenueBreakdown)
async def get_revenue_breakdown(fiscal_year: Optional[str] = None):
    """Get complete revenue breakdown by source."""
    # TODO: Fetch from database
    total = 2_850_000_000
    return RevenueBreakdown(
        fiscal_year="2024/25",
        total_revenue=total,
        sources=[
            RevenueSource(
                name="Value Added Tax (VAT)",
                amount=1_100_000_000,
                percent_of_total=38.6,
                change_yoy=6.5,
            ),
            RevenueSource(
                name="Customs & Import Duties",
                amount=650_000_000,
                percent_of_total=22.8,
                change_yoy=4.2,
            ),
            RevenueSource(
                name="Tourism Taxes & Fees",
                amount=420_000_000,
                percent_of_total=14.7,
                change_yoy=12.5,
            ),
            RevenueSource(
                name="Business License Fees",
                amount=280_000_000,
                percent_of_total=9.8,
                change_yoy=3.8,
            ),
            RevenueSource(
                name="Property Tax",
                amount=150_000_000,
                percent_of_total=5.3,
                change_yoy=2.1,
            ),
            RevenueSource(
                name="Stamp Tax",
                amount=120_000_000,
                percent_of_total=4.2,
                change_yoy=1.5,
            ),
            RevenueSource(
                name="Other Revenue",
                amount=130_000_000,
                percent_of_total=4.6,
                change_yoy=5.0,
            ),
        ],
        last_updated=date.today(),
        source_document="Budget Book 2024-25.pdf",
    )


@router.get("/monthly")
async def get_revenue_monthly(fiscal_year: Optional[str] = None):
    """Get monthly revenue collection data."""
    # TODO: Fetch from database
    return {
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


@router.get("/historical")
async def get_revenue_historical(years: int = 5):
    """Get historical revenue trends."""
    # TODO: Fetch from database
    return {
        "years": [
            {
                "year": "2020/21",
                "total": 2_100_000_000,
                "vat": 780_000_000,
                "customs": 520_000_000,
                "tourism": 280_000_000,
            },
            {
                "year": "2021/22",
                "total": 2_400_000_000,
                "vat": 900_000_000,
                "customs": 580_000_000,
                "tourism": 340_000_000,
            },
            {
                "year": "2022/23",
                "total": 2_650_000_000,
                "vat": 1_000_000_000,
                "customs": 620_000_000,
                "tourism": 380_000_000,
            },
            {
                "year": "2023/24",
                "total": 2_750_000_000,
                "vat": 1_050_000_000,
                "customs": 640_000_000,
                "tourism": 400_000_000,
            },
            {
                "year": "2024/25",
                "total": 2_850_000_000,
                "vat": 1_100_000_000,
                "customs": 650_000_000,
                "tourism": 420_000_000,
            },
        ]
    }


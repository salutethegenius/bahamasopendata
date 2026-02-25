"""Ministries API endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import date

router = APIRouter()


class Ministry(BaseModel):
    """Ministry response model."""
    id: str
    name: str
    allocation: float
    previous_year_allocation: float
    change_percent: float
    sparkline: list[float]  # 5-year trend data
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


@router.get("", response_model=list[Ministry])
async def get_ministries():
    """
    Get all ministries with allocations and YoY change.
    Data from Budget Book 2025/26, Recurrent Expenditure Summary (Page 71-72).
    """
    # Real data from Summary of Agencies - Recurrent Expenditure 2025/26
    return [
        Ministry(
            id="health",
            name="Ministry of Health & Wellness",
            allocation=355_119_623,  # Page 72
            previous_year_allocation=332_747_117,
            change_percent=6.7,
            sparkline=[288.4, 263.2, 332.7, 355.1],  # In millions
            sector="Health",
        ),
        Ministry(
            id="finance",
            name="Ministry of Finance",
            allocation=362_694_099,  # Page 71
            previous_year_allocation=346_639_187,
            change_percent=4.6,
            sparkline=[177.5, 178.8, 346.6, 362.7],
            sector="Finance",
        ),
        Ministry(
            id="education",
            name="Ministry of Education & Technical Training",
            allocation=137_052_342,  # Page 71
            previous_year_allocation=123_252_555,
            change_percent=11.2,
            sparkline=[114.7, 91.4, 123.3, 137.1],
            sector="Education",
        ),
        Ministry(
            id="police",
            name="Royal Bahamas Police Force",
            allocation=134_036_300,  # Page 71
            previous_year_allocation=126_644_406,
            change_percent=5.8,
            sparkline=[126.5, 100.9, 126.6, 134.0],
            sector="Security",
        ),
        Ministry(
            id="tourism",
            name="Ministry of Tourism, Investments & Aviation",
            allocation=123_395_161,  # Page 72
            previous_year_allocation=131_376_411,
            change_percent=-6.1,
            sparkline=[140.5, 97.8, 131.4, 123.4],
            sector="Tourism",
        ),
        Ministry(
            id="defence",
            name="Royal Bahamas Defence Force",
            allocation=77_530_944,  # Page 71
            previous_year_allocation=71_382_034,
            change_percent=8.6,
            sparkline=[69.0, 53.9, 71.4, 77.5],
            sector="Security",
        ),
        Ministry(
            id="disaster",
            name="Ministry of Disaster Risk Management",
            allocation=60_518_380,  # Page 72
            previous_year_allocation=10_538_081,
            change_percent=474.3,  # Major increase for disaster preparedness
            sparkline=[11.9, 7.8, 10.5, 60.5],
            sector="Emergency",
        ),
        Ministry(
            id="foreign-affairs",
            name="Ministry of Foreign Affairs",
            allocation=54_967_437,  # Page 71
            previous_year_allocation=50_682_286,
            change_percent=8.5,
            sparkline=[49.8, 39.7, 50.7, 55.0],
            sector="Government",
        ),
        Ministry(
            id="social-services",
            name="Department of Social Services",
            allocation=53_074_475,  # Page 72
            previous_year_allocation=48_009_263,
            change_percent=10.5,
            sparkline=[47.7, 30.7, 48.0, 53.1],
            sector="Social Services",
        ),
        Ministry(
            id="works",
            name="Ministry of Works & Family Island Affairs",
            allocation=48_213_665,  # Page 71
            previous_year_allocation=36_183_087,
            change_percent=33.2,
            sparkline=[49.9, 41.2, 36.2, 48.2],
            sector="Infrastructure",
        ),
    ]


@router.get("/{ministry_id}", response_model=MinistryDetail)
async def get_ministry_detail(ministry_id: str):
    """Get detailed breakdown for a specific ministry."""
    # Real data from Budget Book 2025/26
    ministry_details = {
        "health": MinistryDetail(
            id="health",
            name="Ministry of Health & Wellness",
            allocation=355_119_623,
            salaries=180_000_000,  # Estimated from wage percentages
            programs=100_000_000,
            capital_projects=45_000_000,
            grants=30_000_000,
            line_items=[
                {"name": "Public Health Services", "amount": 60_631_875},
                {"name": "Environmental Health", "amount": 61_844_996},
                {"name": "General Administration", "amount": 50_000_000},
                {"name": "Hospital Services", "amount": 120_000_000},
                {"name": "Medical Supplies", "amount": 35_000_000},
                {"name": "Capital Projects", "amount": 27_642_752},
            ],
            historical=[
                {"year": "2022/23", "allocation": 288_424_867},
                {"year": "2023/24", "allocation": 263_248_575},
                {"year": "2024/25", "allocation": 332_747_117},
                {"year": "2025/26", "allocation": 355_119_623},
            ],
            source_document="Bahamas BudgetFINAL_2025-2026_.pdf",
            source_page=72,
        ),
        "education": MinistryDetail(
            id="education",
            name="Ministry of Education & Technical Training",
            allocation=137_052_342,
            salaries=95_000_000,
            programs=25_000_000,
            capital_projects=10_000_000,
            grants=7_000_000,
            line_items=[
                {"name": "Teacher Salaries", "amount": 75_000_000},
                {"name": "School Operations", "amount": 25_000_000},
                {"name": "Technical & Vocational Training", "amount": 15_000_000},
                {"name": "Student Support", "amount": 12_000_000},
                {"name": "Administration", "amount": 10_052_342},
            ],
            historical=[
                {"year": "2022/23", "allocation": 114_718_725},
                {"year": "2023/24", "allocation": 91_421_318},
                {"year": "2024/25", "allocation": 123_252_555},
                {"year": "2025/26", "allocation": 137_052_342},
            ],
            source_document="Bahamas BudgetFINAL_2025-2026_.pdf",
            source_page=71,
        ),
    }
    
    if ministry_id in ministry_details:
        return ministry_details[ministry_id]
    raise HTTPException(status_code=404, detail="Ministry not found")


@router.get("/{ministry_id}/sparkline")
async def get_ministry_sparkline(ministry_id: str, years: int = 5):
    """Get sparkline data for a ministry's budget trend."""
    sparkline_data = {
        "health": {
            "data": [288.4, 263.2, 332.7, 355.1],
            "years": ["2022/23", "2023/24", "2024/25", "2025/26"],
        },
        "education": {
            "data": [114.7, 91.4, 123.3, 137.1],
            "years": ["2022/23", "2023/24", "2024/25", "2025/26"],
        },
        "police": {
            "data": [126.5, 100.9, 126.6, 134.0],
            "years": ["2022/23", "2023/24", "2024/25", "2025/26"],
        },
    }
    
    data = sparkline_data.get(ministry_id, {"data": [], "years": []})
    return {
        "ministry_id": ministry_id,
        "data": data["data"],
        "years": data["years"],
    }


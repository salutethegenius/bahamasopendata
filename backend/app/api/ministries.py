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
    """Get all ministries with allocations and YoY change."""
    # TODO: Fetch from database
    return [
        Ministry(
            id="education",
            name="Ministry of Education",
            allocation=450_000_000,
            previous_year_allocation=420_000_000,
            change_percent=7.1,
            sparkline=[380, 395, 410, 420, 450],
            sector="Education",
        ),
        Ministry(
            id="health",
            name="Ministry of Health",
            allocation=380_000_000,
            previous_year_allocation=350_000_000,
            change_percent=8.6,
            sparkline=[310, 325, 340, 350, 380],
            sector="Health",
        ),
        Ministry(
            id="national-security",
            name="Ministry of National Security",
            allocation=320_000_000,
            previous_year_allocation=310_000_000,
            change_percent=3.2,
            sparkline=[280, 290, 300, 310, 320],
            sector="Security",
        ),
        Ministry(
            id="works",
            name="Ministry of Works & Infrastructure",
            allocation=280_000_000,
            previous_year_allocation=250_000_000,
            change_percent=12.0,
            sparkline=[200, 220, 235, 250, 280],
            sector="Infrastructure",
        ),
        Ministry(
            id="finance",
            name="Ministry of Finance",
            allocation=250_000_000,
            previous_year_allocation=245_000_000,
            change_percent=2.0,
            sparkline=[220, 230, 238, 245, 250],
            sector="Finance",
        ),
        Ministry(
            id="tourism",
            name="Ministry of Tourism",
            allocation=180_000_000,
            previous_year_allocation=165_000_000,
            change_percent=9.1,
            sparkline=[140, 150, 158, 165, 180],
            sector="Tourism",
        ),
        Ministry(
            id="social-services",
            name="Ministry of Social Services",
            allocation=150_000_000,
            previous_year_allocation=140_000_000,
            change_percent=7.1,
            sparkline=[120, 128, 135, 140, 150],
            sector="Social Services",
        ),
        Ministry(
            id="agriculture",
            name="Ministry of Agriculture",
            allocation=85_000_000,
            previous_year_allocation=80_000_000,
            change_percent=6.3,
            sparkline=[65, 70, 75, 80, 85],
            sector="Agriculture",
        ),
        Ministry(
            id="environment",
            name="Ministry of Environment",
            allocation=65_000_000,
            previous_year_allocation=58_000_000,
            change_percent=12.1,
            sparkline=[45, 50, 54, 58, 65],
            sector="Environment",
        ),
        Ministry(
            id="pmo",
            name="Office of the Prime Minister",
            allocation=120_000_000,
            previous_year_allocation=115_000_000,
            change_percent=4.3,
            sparkline=[100, 105, 110, 115, 120],
            sector="Executive",
        ),
    ]


@router.get("/{ministry_id}", response_model=MinistryDetail)
async def get_ministry_detail(ministry_id: str):
    """Get detailed breakdown for a specific ministry."""
    # TODO: Fetch from database
    if ministry_id == "education":
        return MinistryDetail(
            id="education",
            name="Ministry of Education",
            allocation=450_000_000,
            salaries=280_000_000,
            programs=95_000_000,
            capital_projects=55_000_000,
            grants=20_000_000,
            line_items=[
                {"name": "Teacher Salaries", "amount": 180_000_000},
                {"name": "Administrative Staff", "amount": 45_000_000},
                {"name": "School Maintenance", "amount": 35_000_000},
                {"name": "Curriculum Development", "amount": 25_000_000},
                {"name": "Student Support Programs", "amount": 20_000_000},
                {"name": "Technology & Equipment", "amount": 18_000_000},
                {"name": "School Construction", "amount": 45_000_000},
                {"name": "Training Programs", "amount": 15_000_000},
            ],
            historical=[
                {"year": "2020/21", "allocation": 380_000_000},
                {"year": "2021/22", "allocation": 395_000_000},
                {"year": "2022/23", "allocation": 410_000_000},
                {"year": "2023/24", "allocation": 420_000_000},
                {"year": "2024/25", "allocation": 450_000_000},
            ],
            source_document="Budget Book 2024-25.pdf",
            source_page=87,
        )
    raise HTTPException(status_code=404, detail="Ministry not found")


@router.get("/{ministry_id}/sparkline")
async def get_ministry_sparkline(ministry_id: str, years: int = 5):
    """Get sparkline data for a ministry's budget trend."""
    # TODO: Fetch from database
    return {
        "ministry_id": ministry_id,
        "data": [380, 395, 410, 420, 450],
        "years": ["2020/21", "2021/22", "2022/23", "2023/24", "2024/25"],
    }


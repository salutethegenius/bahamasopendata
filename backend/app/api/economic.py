"""Economic Indicators API endpoints."""
from datetime import date
from typing import Optional, List, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.db.database import get_db
from app.db.models import (
    EconomicIndicator as EconomicIndicatorModel,
    PublishedEconomicIndicator as PublishedEconomicIndicatorModel,
)

router = APIRouter()


class IncomeBreakdown(BaseModel):
    """Income breakdown by category."""
    food: Optional[float] = None
    housing_utilities: Optional[float] = None
    nfnh: Optional[float] = None  # Non-food, non-housing
    savings: Optional[float] = None


class EconomicIndicator(BaseModel):
    """Economic indicator response model."""
    id: Optional[int] = None
    indicator_type: str  # "middle_class", "working_class"
    island: str  # "new_providence", "grand_bahama"
    year: int
    month_amount: float
    annual_amount: float
    breakdown: Optional[IncomeBreakdown] = None
    source_document: Optional[str] = None
    source_url: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[date] = None


class IncomeComparison(BaseModel):
    """Comparison between middle class and working class."""
    island: str
    year: int
    middle_class: EconomicIndicator
    working_class: EconomicIndicator
    difference_percent: float
    difference_amount: float


def _serialize_indicator(model: EconomicIndicatorModel | PublishedEconomicIndicatorModel) -> EconomicIndicator:
    return EconomicIndicator(
        id=model.id,
        indicator_type=model.indicator_type,
        island=model.island,
        year=model.year,
        month_amount=model.month_amount,
        annual_amount=model.annual_amount,
        breakdown=model.breakdown,
        source_document=model.source_document,
        source_url=model.source_url,
        author=model.author,
        published_date=model.published_date,
    )


async def _db_indicators(
    db,
    *,
    indicator_type: Optional[str] = None,
    island: Optional[str] = None,
    year: Optional[int] = None,
) -> list[EconomicIndicator]:
    for model in (PublishedEconomicIndicatorModel, EconomicIndicatorModel):
        query = select(model)
        if indicator_type:
            query = query.where(model.indicator_type == indicator_type)
        if island:
            query = query.where(model.island == island)
        if year:
            query = query.where(model.year == year)
        query = query.order_by(model.year.desc(), model.island.asc())
        result = await db.execute(query)
        rows = result.scalars().all()
        if rows:
            return [_serialize_indicator(row) for row in rows]
    return []


# Mock data based on the 2024 study
# TODO: Replace with database queries
MOCK_DATA = {
    "new_providence": {
        "middle_class": {
            "indicator_type": "middle_class",
            "island": "new_providence",
            "year": 2024,
            "month_amount": 10200.0,
            "annual_amount": 122400.0,
            "breakdown": {
                "food": 2500.0,
                "housing_utilities": 2142.0,
                "nfnh": 3508.0,
                "savings": 2040.0
            },
            "source_document": "How Much Does It Cost to Be Middle Class in The Bahamas?",
            "source_url": "https://www.ub.edu.bs/wp-content/uploads/Archer2024Final.pdf",
            "author": "Lesvie Archer",
            "published_date": date(2024, 3, 1)
        },
        "working_class": {
            "indicator_type": "working_class",
            "island": "new_providence",
            "year": 2024,
            "month_amount": 5000.0,
            "annual_amount": 60000.0,
            "breakdown": None,
            "source_document": "The Bahamas Living Wages Survey (updated to 2024)",
            "source_url": "https://www.ub.edu.bs/wp-content/uploads/2016/10/GPPI_Living-Wage-Survey_revised_27-May-2021.pdf",
            "author": "Lesvie Archer et al.",
            "published_date": date(2020, 3, 1)
        }
    },
    "grand_bahama": {
        "middle_class": {
            "indicator_type": "middle_class",
            "island": "grand_bahama",
            "year": 2024,
            "month_amount": 10100.0,
            "annual_amount": 121200.0,
            "breakdown": {
                "food": 2850.0,
                "housing_utilities": 1692.0,
                "nfnh": 3508.0,
                "savings": 2020.0
            },
            "source_document": "How Much Does It Cost to Be Middle Class in The Bahamas?",
            "source_url": "https://www.ub.edu.bs/wp-content/uploads/Archer2024Final.pdf",
            "author": "Lesvie Archer",
            "published_date": date(2024, 3, 1)
        },
        "working_class": {
            "indicator_type": "working_class",
            "island": "grand_bahama",
            "year": 2024,
            "month_amount": 6600.0,
            "annual_amount": 79200.0,
            "breakdown": None,
            "source_document": "The Bahamas Living Wages Survey (updated to 2024)",
            "source_url": "https://www.ub.edu.bs/wp-content/uploads/2016/10/GPPI_Living-Wage-Survey_revised_27-May-2021.pdf",
            "author": "Lesvie Archer et al.",
            "published_date": date(2020, 3, 1)
        }
    }
}


@router.get("/indicators", response_model=List[EconomicIndicator])
async def get_all_indicators(
    indicator_type: Optional[str] = None,
    island: Optional[str] = None,
    year: Optional[int] = None,
    db=Depends(get_db),
):
    """
    Get all economic indicators.
    
    Optional filters:
    - indicator_type: "middle_class" or "working_class"
    - island: "new_providence" or "grand_bahama"
    - year: Filter by year
    """
    db_results = await _db_indicators(
        db,
        indicator_type=indicator_type,
        island=island,
        year=year,
    )
    if db_results:
        return db_results

    results = []
    
    for island_key, island_data in MOCK_DATA.items():
        if island and island_key != island:
            continue
            
        for class_type, data in island_data.items():
            if indicator_type and class_type != indicator_type:
                continue
            if year and data["year"] != year:
                continue
                
            indicator = EconomicIndicator(**data)
            results.append(indicator)
    
    return results


@router.get("/indicators/{island}", response_model=List[EconomicIndicator])
async def get_indicators_by_island(island: str, db=Depends(get_db)):
    """
    Get all economic indicators for a specific island.
    
    Island options: "new_providence" or "grand_bahama"
    """
    if island not in MOCK_DATA:
        raise HTTPException(status_code=404, detail=f"Island '{island}' not found")
    
    db_results = await _db_indicators(db, island=island)
    if db_results:
        return db_results

    results = []
    for class_type, data in MOCK_DATA[island].items():
        indicator = EconomicIndicator(**data)
        results.append(indicator)
    
    return results


@router.get("/indicators/{island}/{indicator_type}", response_model=EconomicIndicator)
async def get_specific_indicator(island: str, indicator_type: str, db=Depends(get_db)):
    """
    Get a specific economic indicator.
    
    Island options: "new_providence" or "grand_bahama"
    Indicator type options: "middle_class" or "working_class"
    """
    if island not in MOCK_DATA:
        raise HTTPException(status_code=404, detail=f"Island '{island}' not found")
    
    if indicator_type not in MOCK_DATA[island]:
        raise HTTPException(status_code=404, detail=f"Indicator type '{indicator_type}' not found for {island}")
    
    db_results = await _db_indicators(db, island=island, indicator_type=indicator_type)
    if db_results:
        return db_results[0]

    data = MOCK_DATA[island][indicator_type]
    return EconomicIndicator(**data)


@router.get("/comparison", response_model=List[IncomeComparison])
async def get_comparison(
    island: Optional[str] = None,
    year: Optional[int] = None,
    db=Depends(get_db),
):
    """
    Compare middle class vs working class income requirements.
    
    Optional filters:
    - island: "new_providence" or "grand_bahama" (if not provided, returns both)
    - year: Filter by year
    """
    db_results = await _db_indicators(db, year=year)
    if db_results:
        grouped: Dict[str, Dict[str, EconomicIndicator]] = {}
        for indicator in db_results:
            if island and indicator.island != island:
                continue
            grouped.setdefault(indicator.island, {})[indicator.indicator_type] = indicator

        comparisons: List[IncomeComparison] = []
        for island_key, records in grouped.items():
            middle_class = records.get("middle_class")
            working_class = records.get("working_class")
            if not middle_class or not working_class:
                continue
            difference_amount = middle_class.month_amount - working_class.month_amount
            difference_percent = (
                (difference_amount / working_class.month_amount) * 100
                if working_class.month_amount
                else 0.0
            )
            comparisons.append(
                IncomeComparison(
                    island=island_key,
                    year=middle_class.year,
                    middle_class=middle_class,
                    working_class=working_class,
                    difference_percent=round(difference_percent, 2),
                    difference_amount=round(difference_amount, 2),
                )
            )
        if comparisons:
            return comparisons

    results = []
    
    islands_to_process = [island] if island else list(MOCK_DATA.keys())
    
    for island_key in islands_to_process:
        if island_key not in MOCK_DATA:
            continue
            
        island_data = MOCK_DATA[island_key]
        middle_class_data = island_data["middle_class"]
        working_class_data = island_data["working_class"]
        
        if year and (middle_class_data["year"] != year or working_class_data["year"] != year):
            continue
        
        middle_class = EconomicIndicator(**middle_class_data)
        working_class = EconomicIndicator(**working_class_data)
        
        difference_amount = middle_class.month_amount - working_class.month_amount
        difference_percent = (difference_amount / working_class.month_amount) * 100
        
        comparison = IncomeComparison(
            island=island_key,
            year=middle_class.year,
            middle_class=middle_class,
            working_class=working_class,
            difference_percent=round(difference_percent, 2),
            difference_amount=round(difference_amount, 2)
        )
        results.append(comparison)
    
    return results

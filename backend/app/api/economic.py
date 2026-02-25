"""Economic Indicators API endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import date

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
    year: Optional[int] = None
):
    """
    Get all economic indicators.
    
    Optional filters:
    - indicator_type: "middle_class" or "working_class"
    - island: "new_providence" or "grand_bahama"
    - year: Filter by year
    """
    # TODO: Fetch from database
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
async def get_indicators_by_island(island: str):
    """
    Get all economic indicators for a specific island.
    
    Island options: "new_providence" or "grand_bahama"
    """
    if island not in MOCK_DATA:
        raise HTTPException(status_code=404, detail=f"Island '{island}' not found")
    
    # TODO: Fetch from database
    results = []
    for class_type, data in MOCK_DATA[island].items():
        indicator = EconomicIndicator(**data)
        results.append(indicator)
    
    return results


@router.get("/indicators/{island}/{indicator_type}", response_model=EconomicIndicator)
async def get_specific_indicator(island: str, indicator_type: str):
    """
    Get a specific economic indicator.
    
    Island options: "new_providence" or "grand_bahama"
    Indicator type options: "middle_class" or "working_class"
    """
    if island not in MOCK_DATA:
        raise HTTPException(status_code=404, detail=f"Island '{island}' not found")
    
    if indicator_type not in MOCK_DATA[island]:
        raise HTTPException(status_code=404, detail=f"Indicator type '{indicator_type}' not found for {island}")
    
    # TODO: Fetch from database
    data = MOCK_DATA[island][indicator_type]
    return EconomicIndicator(**data)


@router.get("/comparison", response_model=List[IncomeComparison])
async def get_comparison(island: Optional[str] = None, year: Optional[int] = None):
    """
    Compare middle class vs working class income requirements.
    
    Optional filters:
    - island: "new_providence" or "grand_bahama" (if not provided, returns both)
    - year: Filter by year
    """
    # TODO: Fetch from database
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

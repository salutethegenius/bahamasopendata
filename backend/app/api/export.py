"""Data export API endpoints."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional
import json
import io

router = APIRouter()


@router.get("/{dataset}")
async def export_dataset(
    dataset: str,
    format: str = "json",
    fiscal_year: Optional[str] = None,
):
    """
    Export a dataset in JSON or CSV format.
    
    Available datasets:
    - budget_summary
    - ministries
    - revenue
    - debt
    - historical
    """
    # TODO: Fetch real data from database
    
    datasets = {
        "budget_summary": {
            "data": [
                {
                    "fiscal_year": "2024/25",
                    "total_revenue": 2850000000,
                    "total_expenditure": 3200000000,
                    "deficit_surplus": -350000000,
                    "national_debt": 11500000000,
                    "debt_to_gdp_ratio": 82.5,
                }
            ],
            "source": "Budget Communication 2024-25.pdf",
        },
        "ministries": {
            "data": [
                {"name": "Ministry of Education", "allocation": 450000000, "change_yoy": 7.1},
                {"name": "Ministry of Health", "allocation": 380000000, "change_yoy": 8.6},
                {"name": "Ministry of National Security", "allocation": 320000000, "change_yoy": 3.2},
                {"name": "Ministry of Works & Infrastructure", "allocation": 280000000, "change_yoy": 12.0},
                {"name": "Ministry of Finance", "allocation": 250000000, "change_yoy": 2.0},
                {"name": "Ministry of Tourism", "allocation": 180000000, "change_yoy": 9.1},
                {"name": "Ministry of Social Services", "allocation": 150000000, "change_yoy": 7.1},
                {"name": "Ministry of Agriculture", "allocation": 85000000, "change_yoy": 6.3},
                {"name": "Ministry of Environment", "allocation": 65000000, "change_yoy": 12.1},
                {"name": "Office of the Prime Minister", "allocation": 120000000, "change_yoy": 4.3},
            ],
            "source": "Budget Book 2024-25.pdf",
        },
        "revenue": {
            "data": [
                {"source": "Value Added Tax (VAT)", "amount": 1100000000, "percent_of_total": 38.6},
                {"source": "Customs & Import Duties", "amount": 650000000, "percent_of_total": 22.8},
                {"source": "Tourism Taxes & Fees", "amount": 420000000, "percent_of_total": 14.7},
                {"source": "Business License Fees", "amount": 280000000, "percent_of_total": 9.8},
                {"source": "Property Tax", "amount": 150000000, "percent_of_total": 5.3},
                {"source": "Stamp Tax", "amount": 120000000, "percent_of_total": 4.2},
                {"source": "Other Revenue", "amount": 130000000, "percent_of_total": 4.6},
            ],
            "source": "Budget Book 2024-25.pdf",
        },
        "debt": {
            "data": [
                {
                    "fiscal_year": "2024/25",
                    "total_debt": 11500000000,
                    "domestic_debt": 6200000000,
                    "external_debt": 5300000000,
                    "debt_to_gdp_ratio": 82.5,
                    "annual_interest_cost": 580000000,
                }
            ],
            "source": "Debt Report 2024-25.pdf",
        },
    }
    
    if dataset not in datasets:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset '{dataset}' not found. Available: {list(datasets.keys())}",
        )
    
    data = datasets[dataset]
    
    if format == "json":
        return {
            "dataset": dataset,
            "fiscal_year": fiscal_year or "2024/25",
            "source": data["source"],
            "data": data["data"],
            "download_note": "Data from Bahamas Open Data - https://bahamasopendata.com",
        }
    
    elif format == "csv":
        # Generate CSV
        import csv
        output = io.StringIO()
        if data["data"]:
            writer = csv.DictWriter(output, fieldnames=data["data"][0].keys())
            writer.writeheader()
            writer.writerows(data["data"])
        
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={dataset}.csv"},
        )
    
    else:
        raise HTTPException(status_code=400, detail="Format must be 'json' or 'csv'")


@router.get("")
async def list_datasets():
    """List all available datasets for export."""
    return {
        "datasets": [
            {"name": "budget_summary", "description": "Overall budget summary with revenue, expenditure, and debt"},
            {"name": "ministries", "description": "All ministry allocations with YoY change"},
            {"name": "revenue", "description": "Revenue breakdown by source"},
            {"name": "debt", "description": "National debt breakdown"},
        ],
        "formats": ["json", "csv"],
    }


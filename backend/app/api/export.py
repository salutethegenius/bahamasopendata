"""Data export API endpoints."""
from __future__ import annotations

import csv
import io
import json
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import (
    BudgetItem,
    Creditor,
    Debt,
    IslandAllocation,
    IslandProject,
    Ministry,
    MinistryAllocation,
    PublishedEconomicIndicator,
    PublishedNewsItem,
    Revenue,
)

router = APIRouter()


def _fy_sort_key(fiscal_year: str | None) -> int:
    if not fiscal_year:
        return 0
    try:
        return int(str(fiscal_year).split("/")[0])
    except ValueError:
        return 0


async def _current_year(db: AsyncSession) -> str | None:
    years: set[str] = set()
    for model in (Revenue, MinistryAllocation, Debt, BudgetItem):
        result = await db.execute(select(model.fiscal_year))
        years.update(value for value in result.scalars().all() if value)
    sorted_years = sorted(years, key=_fy_sort_key)
    return sorted_years[-1] if sorted_years else None


async def _budget_summary_rows(db: AsyncSession, fiscal_year: str) -> list[dict[str, Any]]:
    revenue_result = await db.execute(
        select(func.coalesce(func.sum(Revenue.amount), 0.0)).where(Revenue.fiscal_year == fiscal_year)
    )
    expenditure_result = await db.execute(
        select(func.coalesce(func.sum(MinistryAllocation.total_allocation), 0.0)).where(
            MinistryAllocation.fiscal_year == fiscal_year
        )
    )
    debt_result = await db.execute(
        select(Debt).where(Debt.fiscal_year == fiscal_year).order_by(Debt.created_at.desc())
    )
    debt_row = debt_result.scalars().first()
    total_revenue = float(revenue_result.scalar() or 0.0)
    total_expenditure = float(expenditure_result.scalar() or 0.0)

    return [
        {
            "fiscal_year": fiscal_year,
            "total_revenue": total_revenue,
            "total_expenditure": total_expenditure,
            "deficit_surplus": total_revenue - total_expenditure,
            "national_debt": float(debt_row.total_debt or 0.0) if debt_row else 0.0,
            "debt_to_gdp_ratio": float(debt_row.debt_to_gdp_ratio or 0.0) if debt_row else 0.0,
            "annual_interest_cost": float(debt_row.annual_interest or 0.0) if debt_row else 0.0,
        }
    ]


async def _ministries_rows(db: AsyncSession, fiscal_year: str) -> list[dict[str, Any]]:
    current_result = await db.execute(
        select(Ministry.name, MinistryAllocation.total_allocation, MinistryAllocation.ministry_id)
        .join(MinistryAllocation, MinistryAllocation.ministry_id == Ministry.id)
        .where(MinistryAllocation.fiscal_year == fiscal_year)
        .order_by(MinistryAllocation.total_allocation.desc())
    )
    rows = current_result.all()
    previous_year = None
    years_result = await db.execute(select(MinistryAllocation.fiscal_year))
    years = sorted({value for value in years_result.scalars().all() if value}, key=_fy_sort_key)
    if fiscal_year in years:
      idx = years.index(fiscal_year)
      if idx > 0:
        previous_year = years[idx - 1]

    previous_map: dict[int, float] = {}
    if previous_year:
        previous_result = await db.execute(
            select(MinistryAllocation.ministry_id, MinistryAllocation.total_allocation).where(
                MinistryAllocation.fiscal_year == previous_year
            )
        )
        previous_map = {
            ministry_id: float(total or 0.0)
            for ministry_id, total in previous_result.all()
        }

    output: list[dict[str, Any]] = []
    for name, total_allocation, ministry_id in rows:
        previous_total = previous_map.get(ministry_id, 0.0)
        change_yoy = (
            ((float(total_allocation or 0.0) - previous_total) / previous_total) * 100
            if previous_total
            else 0.0
        )
        output.append(
            {
                "name": name,
                "allocation": float(total_allocation or 0.0),
                "change_yoy": round(change_yoy, 1),
            }
        )
    return output


async def _revenue_rows(db: AsyncSession, fiscal_year: str) -> list[dict[str, Any]]:
    total_result = await db.execute(
        select(func.coalesce(func.sum(Revenue.amount), 0.0)).where(Revenue.fiscal_year == fiscal_year)
    )
    total_revenue = float(total_result.scalar() or 0.0)
    result = await db.execute(
        select(Revenue.source_name, Revenue.amount)
        .where(Revenue.fiscal_year == fiscal_year)
        .order_by(Revenue.amount.desc())
    )
    return [
        {
            "source": source_name,
            "amount": float(amount or 0.0),
            "percent_of_total": round((float(amount or 0.0) / total_revenue) * 100, 1)
            if total_revenue
            else 0.0,
        }
        for source_name, amount in result.all()
    ]


async def _debt_rows(db: AsyncSession, fiscal_year: str) -> list[dict[str, Any]]:
    result = await db.execute(
        select(Creditor.name, Creditor.category, Creditor.amount_owed)
        .where(Creditor.fiscal_year == fiscal_year)
        .order_by(Creditor.amount_owed.desc())
    )
    rows = result.all()
    if rows:
        total = sum(float(amount or 0.0) for _, _, amount in rows)
        return [
            {
                "name": name,
                "category": category,
                "amount": float(amount or 0.0),
                "percent_of_total": round((float(amount or 0.0) / total) * 100, 1) if total else 0.0,
            }
            for name, category, amount in rows
        ]

    debt_result = await db.execute(
        select(Debt).where(Debt.fiscal_year == fiscal_year).order_by(Debt.created_at.desc())
    )
    debt_row = debt_result.scalars().first()
    if debt_row is None:
        return []
    return [
        {
            "fiscal_year": fiscal_year,
            "total_debt": float(debt_row.total_debt or 0.0),
            "domestic_debt": float(debt_row.domestic_debt or 0.0),
            "external_debt": float(debt_row.external_debt or 0.0),
            "debt_to_gdp_ratio": float(debt_row.debt_to_gdp_ratio or 0.0),
            "annual_interest_cost": float(debt_row.annual_interest or 0.0),
        }
    ]


async def _historical_rows(db: AsyncSession, years: int = 10) -> list[dict[str, Any]]:
    year_result = await db.execute(select(Debt.fiscal_year))
    fiscal_years = sorted({value for value in year_result.scalars().all() if value}, key=_fy_sort_key)
    output: list[dict[str, Any]] = []
    for fiscal_year in fiscal_years[-years:]:
        revenue_result = await db.execute(
            select(func.coalesce(func.sum(Revenue.amount), 0.0)).where(Revenue.fiscal_year == fiscal_year)
        )
        expenditure_result = await db.execute(
            select(func.coalesce(func.sum(MinistryAllocation.total_allocation), 0.0)).where(
                MinistryAllocation.fiscal_year == fiscal_year
            )
        )
        debt_result = await db.execute(
            select(Debt).where(Debt.fiscal_year == fiscal_year).order_by(Debt.created_at.desc())
        )
        debt_row = debt_result.scalars().first()
        output.append(
            {
                "year": fiscal_year,
                "revenue": float(revenue_result.scalar() or 0.0),
                "expenditure": float(expenditure_result.scalar() or 0.0),
                "debt": float(debt_row.total_debt or 0.0) if debt_row else 0.0,
                "debt_gdp": float(debt_row.debt_to_gdp_ratio or 0.0) if debt_row else 0.0,
            }
        )
    return output


async def _line_item_rows(db: AsyncSession, fiscal_year: str) -> list[dict[str, Any]]:
    result = await db.execute(
        select(BudgetItem.item_name, BudgetItem.category, BudgetItem.amount)
        .where(BudgetItem.fiscal_year == fiscal_year)
        .order_by(BudgetItem.amount.desc())
    )
    return [
        {
            "item_name": item_name,
            "category": category,
            "amount": float(amount or 0.0),
        }
        for item_name, category, amount in result.all()
    ]


async def _news_rows(db: AsyncSession) -> list[dict[str, Any]]:
    result = await db.execute(
        select(PublishedNewsItem).order_by(PublishedNewsItem.published_date.desc(), PublishedNewsItem.created_at.desc())
    )
    return [
        {
            "title": row.title,
            "source": row.source,
            "url": row.url,
            "published_date": row.published_date.isoformat() if row.published_date else None,
            "summary": row.summary,
            "category": row.category,
        }
        for row in result.scalars().all()
    ]


async def _economic_rows(db: AsyncSession) -> list[dict[str, Any]]:
    result = await db.execute(
        select(PublishedEconomicIndicator).order_by(
            PublishedEconomicIndicator.year.desc(),
            PublishedEconomicIndicator.island.asc(),
            PublishedEconomicIndicator.indicator_type.asc(),
        )
    )
    return [
        {
            "indicator_type": row.indicator_type,
            "island": row.island,
            "year": row.year,
            "month_amount": float(row.month_amount or 0.0),
            "annual_amount": float(row.annual_amount or 0.0),
            "source_document": row.source_document,
            "source_url": row.source_url,
        }
        for row in result.scalars().all()
    ]


async def _island_rows(db: AsyncSession) -> list[dict[str, Any]]:
    result = await db.execute(select(IslandAllocation).order_by(IslandAllocation.name.asc()))
    islands = result.scalars().all()
    output: list[dict[str, Any]] = []
    for island in islands:
        projects_result = await db.execute(
            select(IslandProject).where(IslandProject.island_id == island.id).order_by(IslandProject.amount.desc())
        )
        output.append(
            {
                "island_id": island.island_id,
                "name": island.name,
                "capital": island.capital,
                "population": island.population,
                "allocation": float(island.total_allocation or 0.0),
                "project_count": len(projects_result.scalars().all()),
            }
        )
    return output


async def _dataset_payload(db: AsyncSession, dataset: str, fiscal_year: str | None) -> dict[str, Any]:
    current_year = fiscal_year or await _current_year(db)
    if not current_year:
        raise HTTPException(status_code=404, detail="No published data available yet.")

    dataset_builders = {
        "budget_summary": _budget_summary_rows,
        "ministries": _ministries_rows,
        "revenue": _revenue_rows,
        "debt": _debt_rows,
        "historical": _historical_rows,
        "line_items": _line_item_rows,
        "news": _news_rows,
        "economic_indicators": _economic_rows,
        "island_projects": _island_rows,
    }

    if dataset not in dataset_builders:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset '{dataset}' not found. Available: {list(dataset_builders.keys())}",
        )

    if dataset in {"historical", "news", "economic_indicators", "island_projects"}:
        data = await dataset_builders[dataset](db)
    else:
        data = await dataset_builders[dataset](db, current_year)

    if not data:
        raise HTTPException(status_code=404, detail=f"No published rows found for dataset '{dataset}'.")

    return {
        "dataset": dataset,
        "fiscal_year": current_year,
        "generated_at": date.today().isoformat(),
        "data": data,
    }


@router.get("/{dataset}")
async def export_dataset(
    dataset: str,
    format: str = "json",
    fiscal_year: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Export a dataset in JSON or CSV format."""
    payload = await _dataset_payload(db, dataset, fiscal_year)

    if format == "json":
        return payload

    if format != "csv":
        raise HTTPException(status_code=400, detail="Format must be 'json' or 'csv'")

    output = io.StringIO()
    fieldnames = list(payload["data"][0].keys()) if payload["data"] else []
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(payload["data"])
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={dataset}.csv"},
    )


@router.get("")
async def list_datasets(db: AsyncSession = Depends(get_db)):
    """List all available datasets for export."""
    current_year = await _current_year(db)
    datasets = [
        {"name": "budget_summary", "description": "Overall budget summary with revenue, expenditure, and debt"},
        {"name": "ministries", "description": "Published ministry allocations with year-over-year change"},
        {"name": "revenue", "description": "Published revenue breakdown by source"},
        {"name": "debt", "description": "Published debt data and creditor breakdown"},
        {"name": "historical", "description": "Published historical budget and debt trend rows"},
        {"name": "line_items", "description": "Published budget line items for the current fiscal year"},
        {"name": "news", "description": "Published public updates and announcement feed"},
        {"name": "economic_indicators", "description": "Published household economy and affordability indicators"},
        {"name": "island_projects", "description": "Published island allocations and project listings"},
    ]

    availability = []
    for item in datasets:
        try:
            payload = await _dataset_payload(db, item["name"], current_year)
            availability.append(
                {
                    **item,
                    "records": len(payload["data"]),
                    "available": True,
                }
            )
        except HTTPException:
            availability.append({**item, "records": 0, "available": False})

    return {
        "fiscal_year": current_year,
        "datasets": availability,
        "formats": ["json", "csv"],
    }

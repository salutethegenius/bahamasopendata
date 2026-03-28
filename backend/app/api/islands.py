"""Island allocations and project API endpoints."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.db.models import IslandAllocation, IslandProject

router = APIRouter()


class IslandProjectResponse(BaseModel):
    name: str
    amount: float
    category: str | None = None


class IslandResponse(BaseModel):
    id: str
    name: str
    capital: str | None = None
    population: int | None = None
    allocation: float
    projects: List[IslandProjectResponse]
    source_document: str | None = None


async def _load_island_rows(db) -> list[IslandAllocation]:
    result = await db.execute(
        select(IslandAllocation)
        .options(selectinload(IslandAllocation.projects))
        .order_by(IslandAllocation.name.asc())
    )
    return list(result.scalars().all())


def _serialize_island(row: IslandAllocation) -> IslandResponse:
    return IslandResponse(
        id=row.island_id,
        name=row.name,
        capital=row.capital,
        population=row.population,
        allocation=float(row.total_allocation or 0.0),
        projects=[
            IslandProjectResponse(
                name=project.project_name,
                amount=float(project.amount or 0.0),
                category=project.category,
            )
            for project in sorted(row.projects, key=lambda item: (item.category or "", item.project_name))
        ],
        source_document=None,
    )


@router.get("", response_model=List[IslandResponse])
async def list_islands(db=Depends(get_db)):
    rows = await _load_island_rows(db)
    return [_serialize_island(row) for row in rows]


@router.get("/{island_id}", response_model=IslandResponse)
async def get_island(island_id: str, db=Depends(get_db)):
    rows = await _load_island_rows(db)
    for row in rows:
        if row.island_id == island_id:
            return _serialize_island(row)
    raise HTTPException(status_code=404, detail=f"Island '{island_id}' not found")

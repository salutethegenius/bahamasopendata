"""Superuser-only editable roadmap endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_client_ip, require_superuser
from app.db.database import get_db
from app.db.models import AdminUser, AuditLog
from app.services.future_updates import load_future_updates, save_future_updates


router = APIRouter()


class FutureUpdateCard(BaseModel):
    id: str = Field(..., min_length=1, max_length=120)
    title: str = Field(..., min_length=1, max_length=200)
    phase: str = Field(..., min_length=1, max_length=80)
    description: str = Field(..., min_length=1, max_length=2000)
    items: list[str] = Field(default_factory=list)


@router.get("", response_model=list[FutureUpdateCard])
async def get_future_updates(
    current_user: AdminUser = Depends(require_superuser),
) -> list[FutureUpdateCard]:
    """Return editable roadmap cards for the superuser panel."""
    del current_user
    return [FutureUpdateCard.model_validate(item) for item in load_future_updates()]


@router.put("", response_model=list[FutureUpdateCard])
async def update_future_updates(
    payload: list[FutureUpdateCard],
    request: Request,
    current_user: AdminUser = Depends(require_superuser),
    db: AsyncSession = Depends(get_db),
) -> list[FutureUpdateCard]:
    """Replace editable roadmap cards."""
    serialized = [item.model_dump() for item in payload]
    save_future_updates(serialized)

    db.add(
        AuditLog(
            user_id=current_user.id,
            action="update_future_updates",
            resource_type="future_updates",
            resource_id=str(len(serialized)),
            details={"card_count": len(serialized)},
            ip_address=get_client_ip(request),
        )
    )
    await db.commit()

    return [FutureUpdateCard.model_validate(item) for item in serialized]

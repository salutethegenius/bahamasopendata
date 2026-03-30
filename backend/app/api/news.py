"""Official news and announcement endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import NewsItem, PublishedNewsItem

router = APIRouter()


@router.get("")
async def list_news(
    category: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Return official news items, newest first."""
    safe_limit = max(1, min(limit, 200))

    published_query = select(PublishedNewsItem).order_by(
        desc(PublishedNewsItem.published_date),
        desc(PublishedNewsItem.created_at),
    ).limit(safe_limit)

    if category:
        published_query = published_query.where(PublishedNewsItem.category == category)

    published_result = await db.execute(published_query)
    published_rows = published_result.scalars().all()
    if published_rows:
        return [
            {
                "id": row.id,
                "title": row.title,
                "source": row.source or "Official source",
                "url": row.url or "#",
                "published_date": row.published_date.isoformat() if row.published_date else None,
                "summary": row.summary or "",
                "category": row.category or "Other",
            }
            for row in published_rows
        ]

    query = select(NewsItem).order_by(
        desc(NewsItem.published_date),
        desc(NewsItem.created_at),
    ).limit(safe_limit)

    if category:
        query = query.where(NewsItem.category == category)

    result = await db.execute(query)
    rows = result.scalars().all()

    return [
        {
            "id": row.id,
            "title": row.title,
            "source": row.source or "Official source",
            "url": row.url or "#",
            "published_date": row.published_date.isoformat() if row.published_date else None,
            "summary": row.summary or "",
            "category": row.category or "Other",
        }
        for row in rows
    ]

"""Bahamas Open Data API - Civic Finance Dashboard Backend."""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    ask,
    budget,
    debt,
    documents,
    economic,
    export,
    hot_topics,
    ministries,
    polls,
    revenue,
)
from sqlalchemy import select

from app.core.config import settings
from app.db.database import AsyncSessionLocal, engine
from app.db.models import Base, Poll, PollOption

logger = logging.getLogger(__name__)

MAX_DB_RETRIES = 5
RETRY_DELAY_SECONDS = 3


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    print(f"🇧🇸 {settings.APP_NAME} starting up...")

    for attempt in range(1, MAX_DB_RETRIES + 1):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            break
        except Exception as exc:
            if attempt == MAX_DB_RETRIES:
                logger.error("Database unavailable after %d attempts, starting without table sync: %s", MAX_DB_RETRIES, exc)
            else:
                logger.warning("Database connection attempt %d/%d failed: %s – retrying in %ds", attempt, MAX_DB_RETRIES, exc, RETRY_DELAY_SECONDS)
                await asyncio.sleep(RETRY_DELAY_SECONDS)

    # Seed default polls if the table is empty (e.g. fresh deploy / new DB)
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Poll))
            if result.scalars().first() is None:
                poll1 = Poll(
                    question="What should be the top priority for the next national budget?",
                    description="Share your view on where government should focus spending.",
                    status="active",
                    domain="budget",
                )
                session.add(poll1)
                await session.flush()
                for i, text in enumerate([
                    "Healthcare and public health",
                    "Education and training",
                    "Infrastructure (roads, utilities)",
                    "Economic development and jobs",
                    "Public safety and national security",
                ]):
                    session.add(PollOption(poll_id=poll1.id, option_text=text, display_order=i))
                await session.commit()
                logger.info("Seeded default poll (active).")
    except Exception as exc:
        logger.warning("Could not seed default polls: %s", exc)

    yield
    print(f"🇧🇸 {settings.APP_NAME} shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Bahamas Open Data - Public finance data made clear and accessible.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(budget.router, prefix=f"{settings.API_V1_PREFIX}/budget", tags=["Budget"])
app.include_router(ministries.router, prefix=f"{settings.API_V1_PREFIX}/ministries", tags=["Ministries"])
app.include_router(revenue.router, prefix=f"{settings.API_V1_PREFIX}/revenue", tags=["Revenue"])
app.include_router(debt.router, prefix=f"{settings.API_V1_PREFIX}/debt", tags=["Debt"])
app.include_router(ask.router, prefix=f"{settings.API_V1_PREFIX}/ask", tags=["Ask"])
app.include_router(export.router, prefix=f"{settings.API_V1_PREFIX}/export", tags=["Export"])
app.include_router(economic.router, prefix=f"{settings.API_V1_PREFIX}/economic", tags=["Economic"])
app.include_router(documents.router, prefix=f"{settings.API_V1_PREFIX}/documents", tags=["Documents"])
app.include_router(hot_topics.router, prefix=f"{settings.API_V1_PREFIX}/hot-topics", tags=["Hot Topics"])
app.include_router(polls.router, prefix=f"{settings.API_V1_PREFIX}/polls", tags=["Polls"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "description": "Bahamas Open Data - Civic finance dashboard API",
        "version": "1.0.0",
        "website": "https://bahamasopendata.com",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": settings.APP_NAME}


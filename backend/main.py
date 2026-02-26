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
    ministries,
    polls,
    revenue,
)
from app.core.config import settings
from app.db.database import engine
from app.db.models import Base

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


"""Bahamas Open Data API - Civic Finance Dashboard Backend."""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api import (
    auth,
    ask,
    budget,
    debt,
    documents,
    economic,
    export,
    future_updates,
    hot_topics,
    ingestion,
    islands,
    ministries,
    news,
    polls,
    revenue,
)
from sqlalchemy import select

from app.core.config import settings
from app.core.security import ensure_jwt_key_pair, hash_password, validate_password
from app.db.database import AsyncSessionLocal, engine
from app.db.models import AdminUser, Base, Poll, PollOption

logger = logging.getLogger(__name__)

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.RATE_LIMIT_DEFAULT],
    storage_uri="memory://",
)

MAX_DB_RETRIES = 5
RETRY_DELAY_SECONDS = 3


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    print(f"🇧🇸 {settings.APP_NAME} starting up...")
    ensure_jwt_key_pair()

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

    # Seed initial superuser when explicitly configured
    if settings.INITIAL_SUPERUSER_EMAIL and settings.INITIAL_SUPERUSER_PASSWORD:
        try:
            validate_password(settings.INITIAL_SUPERUSER_PASSWORD)
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(AdminUser).where(
                        AdminUser.email == settings.INITIAL_SUPERUSER_EMAIL.lower()
                    )
                )
                if result.scalars().first() is None:
                    session.add(
                        AdminUser(
                            email=settings.INITIAL_SUPERUSER_EMAIL.lower(),
                            hashed_password=hash_password(settings.INITIAL_SUPERUSER_PASSWORD),
                            full_name="Initial Superuser",
                            role="superuser",
                            is_active=True,
                        )
                    )
                    await session.commit()
                    logger.info(
                        "Seeded initial superuser account for %s",
                        settings.INITIAL_SUPERUSER_EMAIL.lower(),
                    )
        except Exception as exc:
            logger.warning("Could not seed initial superuser: %s", exc)

    yield
    print(f"🇧🇸 {settings.APP_NAME} shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Bahamas Open Data - Public finance data made clear and accessible.",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "frame-ancestors 'none'"
    )
    return response

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Auth"])
app.include_router(future_updates.router, prefix=f"{settings.API_V1_PREFIX}/future-updates", tags=["Future Updates"])
app.include_router(budget.router, prefix=f"{settings.API_V1_PREFIX}/budget", tags=["Budget"])
app.include_router(ministries.router, prefix=f"{settings.API_V1_PREFIX}/ministries", tags=["Ministries"])
app.include_router(revenue.router, prefix=f"{settings.API_V1_PREFIX}/revenue", tags=["Revenue"])
app.include_router(debt.router, prefix=f"{settings.API_V1_PREFIX}/debt", tags=["Debt"])
app.include_router(ask.router, prefix=f"{settings.API_V1_PREFIX}/ask", tags=["Ask"])
app.include_router(export.router, prefix=f"{settings.API_V1_PREFIX}/export", tags=["Export"])
app.include_router(economic.router, prefix=f"{settings.API_V1_PREFIX}/economic", tags=["Economic"])
app.include_router(news.router, prefix=f"{settings.API_V1_PREFIX}/news", tags=["News"])
app.include_router(islands.router, prefix=f"{settings.API_V1_PREFIX}/islands", tags=["Islands"])
app.include_router(documents.router, prefix=f"{settings.API_V1_PREFIX}/documents", tags=["Documents"])
app.include_router(ingestion.router, prefix=f"{settings.API_V1_PREFIX}/ingestion", tags=["Ingestion"])
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

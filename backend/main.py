"""Bahamas Open Data API - Civic Finance Dashboard Backend."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api import budget, ministries, revenue, debt, ask, export


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print(f"🇧🇸 {settings.APP_NAME} starting up...")
    yield
    # Shutdown
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


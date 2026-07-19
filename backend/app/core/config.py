"""Application configuration using pydantic-settings."""
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    # App
    APP_NAME: str = "Bahamas Open Data API"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    # OpenAPI /docs — disable in production (ENABLE_OPENAPI=false)
    ENABLE_OPENAPI: bool = False
    # SQL echo: never default True; keep independent of DEBUG (R04)
    SQLALCHEMY_ECHO: bool = False
    # Only seed INITIAL_SUPERUSER_* when explicitly allowed (R09)
    ALLOW_INITIAL_SUPERUSER_BOOTSTRAP: bool = False
    # Dev convenience: auto-create tables from models. Production should use Alembic only (R10).
    ENABLE_METADATA_CREATE_ALL: bool = True
    # Optional Redis URL for shared rate limits across workers (R03); empty = in-memory
    REDIS_URL: str = ""
    # Public Ask endpoint abuse control (R05)
    RATE_LIMIT_ASK: str = "30/minute"
    # HMAC pepper for poll vote fingerprints (R07); set in production
    FINGERPRINT_PEPPER: str = ""
    # httpOnly access JWT cookie name (R01)
    ACCESS_TOKEN_COOKIE_NAME: str = "bod_access_token"

    # Database
    DATABASE_URL: str = "postgresql://localhost:5432/nationalpulse"

    # JWT Authentication
    JWT_PRIVATE_KEY_PATH: str = ""
    JWT_PUBLIC_KEY_PATH: str = ""
    JWT_ALGORITHM: str = "EdDSA"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    COOKIE_SECURE: bool = True
    COOKIE_SAMESITE: str = "none"

    # Trusted proxy
    TRUSTED_PROXY_COUNT: int = 0

    # Initial Superuser (auto-created on first startup if set)
    INITIAL_SUPERUSER_EMAIL: str = ""
    INITIAL_SUPERUSER_PASSWORD: str = ""

    # Rate Limiting
    RATE_LIMIT_DEFAULT: str = "240/minute"
    RATE_LIMIT_ADMIN: str = "60/minute"
    RATE_LIMIT_AUTH: str = "5/minute"

    # Pinecone
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX_NAME: str = "national-pulse"
    PINECONE_ENVIRONMENT: str = "us-east-1"

    # OpenAI
    OPENAI_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    CHAT_MODEL: str = "gpt-4o-mini"

    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # YouTube Data API v3 (Intelligence imprint social capture)
    YOUTUBE_API_KEY: str = ""

    # Bing Web Search v7 (Intelligence imprint non-branded SERP capture)
    BING_SEARCH_API_KEY: str = ""

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://bahamasopendata.com",
        "https://www.bahamasopendata.com",
    ]
    
    class Config:
        # Use absolute path to .env file in backend directory
        env_file = str(Path(__file__).parent.parent.parent / ".env")
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


settings = get_settings()

# Shared rate limiter instance — import from here in routers and main.py
from slowapi import Limiter
from slowapi.util import get_remote_address

_limiter_storage = settings.REDIS_URL.strip() if settings.REDIS_URL.strip() else "memory://"

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.RATE_LIMIT_DEFAULT],
    storage_uri=_limiter_storage,
)

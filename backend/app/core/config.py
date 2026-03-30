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

    # Database
    DATABASE_URL: str = "postgresql://localhost:5432/nationalpulse"

    # JWT Authentication
    JWT_PRIVATE_KEY_PATH: str = ""
    JWT_PUBLIC_KEY_PATH: str = ""
    JWT_ALGORITHM: str = "EdDSA"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    COOKIE_SECURE: bool = True

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

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.RATE_LIMIT_DEFAULT],
    storage_uri="memory://",
)

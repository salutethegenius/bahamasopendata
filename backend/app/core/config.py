"""Application configuration using pydantic-settings."""
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    # Polls
    POLLS_ADMIN_API_KEY: str | None = None  # used to protect /polls admin endpoints
    # App
    APP_NAME: str = "Bahamas Open Data API"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql://localhost:5432/nationalpulse"
    
    # Pinecone
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX_NAME: str = "national-pulse"
    PINECONE_ENVIRONMENT: str = "us-east-1"
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    CHAT_MODEL: str = "gpt-4o-mini"
    
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


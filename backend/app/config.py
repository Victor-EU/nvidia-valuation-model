from urllib.parse import urlparse, urlencode, parse_qs

from pydantic_settings import BaseSettings
from pydantic import model_validator
from functools import lru_cache


def _convert_for_asyncpg(url: str) -> str:
    """Convert a postgresql:// URL to postgresql+asyncpg://, removing sslmode (asyncpg uses ssl param)."""
    url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    # asyncpg doesn't accept sslmode — it's handled via connect_args
    params.pop("sslmode", None)
    new_query = urlencode(params, doseq=True)
    return parsed._replace(query=new_query).geturl()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database - default to SQLite for easy local testing
    database_url: str = "sqlite+aiosqlite:///./nvidia_valuation.db"
    database_url_sync: str = "sqlite:///./nvidia_valuation.db"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False

    # CORS
    cors_origins: list[str] = [
        "http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:3000",
        "https://nvidia-valuation-model.telbase.ai",
    ]

    # SSL for asyncpg (derived from sslmode)
    database_ssl: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @model_validator(mode="after")
    def ensure_async_driver(self):
        """Auto-convert postgresql:// to postgresql+asyncpg://, handling sslmode."""
        if self.database_url.startswith("postgresql://"):
            # Check if sslmode=require was in the original URL
            if "sslmode=require" in self.database_url or "sslmode=verify" in self.database_url:
                self.database_ssl = True
            self.database_url = _convert_for_asyncpg(self.database_url)
        if self.database_url_sync == "sqlite:///./nvidia_valuation.db" and "postgresql" in self.database_url:
            # Derive sync URL from async URL (psycopg2 handles sslmode fine)
            sync_url = self.database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
            # Re-add sslmode for psycopg2
            if self.database_ssl and "sslmode=" not in sync_url:
                sep = "&" if "?" in sync_url else "?"
                sync_url += f"{sep}sslmode=require"
            self.database_url_sync = sync_url
        return self


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

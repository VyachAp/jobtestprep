"""Application configuration with environment variable support."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenWeatherMap API
    openweathermap_api_key: str = ""
    openweathermap_base_url: str = "https://api.openweathermap.org/data/2.5/weather"

    # Storage paths
    data_dir: Path = Path("data")
    logs_dir: Path = Path("logs")

    # Cache settings
    cache_ttl_seconds: int = 300  # 5 minutes

    # Database
    database_url: str = "sqlite+aiosqlite:///logs/events.db"

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_default: str = "100/minute"  # Default rate limit for all endpoints
    rate_limit_weather: str = "30/minute"  # Stricter limit for weather endpoint
    rate_limit_storage_uri: str = "memory://"  # Use Redis URI for production

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Ensure directories exist
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.logs_dir.mkdir(parents=True, exist_ok=True)


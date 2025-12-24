"""Pytest fixtures and configuration for Weather API tests."""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

# Set test environment variables before importing app
os.environ["OPENWEATHERMAP_API_KEY"] = "test_api_key_12345"
os.environ["DATA_DIR"] = tempfile.mkdtemp()
os.environ["LOGS_DIR"] = tempfile.mkdtemp()

from app.main import app
from app.models.weather import WeatherData
from app.services.cache import CacheService
from app.services.event_logger import EventLogger, SQLiteEventLogger
from app.services.storage import LocalFileStorage, StorageService


@pytest.fixture
def sample_weather_data() -> WeatherData:
    """Create sample weather data for testing."""
    return WeatherData(
        city="London",
        country="GB",
        temperature=15.5,
        feels_like=14.0,
        humidity=72,
        pressure=1013,
        wind_speed=5.2,
        description="scattered clouds",
        icon="03d",
        timestamp=datetime(2024, 1, 15, 12, 0, 0),
    )


@pytest.fixture
def sample_weather_api_response() -> dict:
    """Create sample OpenWeatherMap API response for mocking."""
    return {
        "coord": {"lon": -0.1257, "lat": 51.5085},
        "weather": [
            {
                "id": 803,
                "main": "Clouds",
                "description": "broken clouds",
                "icon": "04d",
            }
        ],
        "base": "stations",
        "main": {
            "temp": 12.5,
            "feels_like": 11.2,
            "temp_min": 10.5,
            "temp_max": 14.0,
            "pressure": 1020,
            "humidity": 65,
        },
        "visibility": 10000,
        "wind": {"speed": 4.1, "deg": 240},
        "clouds": {"all": 75},
        "dt": 1705320000,
        "sys": {
            "type": 2,
            "id": 2075535,
            "country": "GB",
            "sunrise": 1705304800,
            "sunset": 1705335600,
        },
        "timezone": 0,
        "id": 2643743,
        "name": "London",
        "cod": 200,
    }


@pytest.fixture
def temp_data_dir(tmp_path) -> Path:
    """Create a temporary data directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def temp_logs_dir(tmp_path) -> Path:
    """Create a temporary logs directory."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    return logs_dir


@pytest.fixture
def cache_service() -> CacheService:
    """Create a cache service instance with short TTL for testing."""
    return CacheService(ttl_seconds=60)


@pytest.fixture
def storage_service(temp_data_dir) -> StorageService:
    """Create a storage service instance with temp directory."""
    storage = LocalFileStorage(base_path=temp_data_dir)
    return StorageService(storage=storage)


@pytest.fixture
def event_logger(temp_logs_dir) -> EventLogger:
    """Create an event logger instance with temp database."""
    db_path = temp_logs_dir / "test_events.db"
    logger = SQLiteEventLogger(db_path=db_path)
    return EventLogger(logger=logger)


@pytest.fixture
def test_client() -> TestClient:
    """Create a synchronous test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Create an async test client for the FastAPI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


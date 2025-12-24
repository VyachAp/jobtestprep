"""Integration tests for the Weather API endpoints."""

import os
import tempfile
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

# Set test environment variables before importing app
os.environ["OPENWEATHERMAP_API_KEY"] = "test_api_key_12345"
os.environ["DATA_DIR"] = tempfile.mkdtemp()
os.environ["LOGS_DIR"] = tempfile.mkdtemp()

from app.dependencies import services
from app.main import app


@pytest.fixture(autouse=True)
def reset_services():
    """Reset services before each test."""
    services.initialize()
    yield


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_check_returns_200(self):
        """Test health endpoint returns 200 OK."""
        client = TestClient(app)

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "weather-api"

    def test_health_check_includes_cache_stats(self):
        """Test health endpoint includes cache statistics."""
        client = TestClient(app)

        response = client.get("/health")

        data = response.json()
        assert "cache_stats" in data
        assert data["cache_stats"]["ttl_seconds"] > 0


class TestEventsEndpoint:
    """Tests for the /events endpoint."""

    def test_events_returns_empty_list_initially(self):
        """Test events endpoint returns empty list when no events."""
        client = TestClient(app)

        response = client.get("/events")

        assert response.status_code == 200
        data = response.json()
        assert data["events"] == []
        assert data["count"] == 0

    def test_events_with_limit_parameter(self):
        """Test events endpoint respects limit parameter."""
        client = TestClient(app)

        response = client.get("/events?limit=50")

        assert response.status_code == 200

    def test_events_with_city_filter(self):
        """Test events endpoint accepts city filter."""
        client = TestClient(app)

        response = client.get("/events?city=London")

        assert response.status_code == 200


class TestWeatherEndpoint:
    """Tests for the /weather endpoint."""

    def test_get_weather_success(self, sample_weather_data):
        """Test successful weather data retrieval."""
        with patch(
            "app.services.weather.WeatherService.get_weather",
            new_callable=AsyncMock,
            return_value=sample_weather_data,
        ):
            client = TestClient(app)
            response = client.get("/weather?city=London")

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["city"] == "London"
            assert data["cached"] is False
            assert "file_path" in data

    def test_get_weather_caching(self, sample_weather_data):
        """Test weather data is cached on second request."""
        with patch(
            "app.services.weather.WeatherService.get_weather",
            new_callable=AsyncMock,
            return_value=sample_weather_data,
        ):
            client = TestClient(app)

            # First request - not cached
            response1 = client.get("/weather?city=London")
            assert response1.status_code == 200
            assert response1.json()["cached"] is False

            # Second request - should be cached
            response2 = client.get("/weather?city=London")
            assert response2.status_code == 200
            assert response2.json()["cached"] is True

    def test_get_weather_city_not_found(self):
        """Test 404 when city is not found."""
        from app.services.weather import CityNotFoundError

        with patch(
            "app.services.weather.WeatherService.get_weather",
            new_callable=AsyncMock,
            side_effect=CityNotFoundError("NonexistentCity12345"),
        ):
            client = TestClient(app)
            response = client.get("/weather?city=NonexistentCity12345")

            assert response.status_code == 404
            data = response.json()
            assert "error" in data
            assert data["type"] == "CityNotFoundError"

    def test_get_weather_invalid_api_key(self):
        """Test 401 when API key is invalid."""
        from app.services.weather import APIKeyError

        with patch(
            "app.services.weather.WeatherService.get_weather",
            new_callable=AsyncMock,
            side_effect=APIKeyError(),
        ):
            client = TestClient(app)
            response = client.get("/weather?city=London")

            assert response.status_code == 401
            data = response.json()
            assert data["type"] == "APIKeyError"

    def test_get_weather_missing_city_param(self):
        """Test validation error when city parameter is missing."""
        client = TestClient(app)

        response = client.get("/weather")

        assert response.status_code == 422  # Validation error

    def test_get_weather_empty_city(self):
        """Test validation error when city is empty."""
        client = TestClient(app)

        response = client.get("/weather?city=")

        assert response.status_code == 422

    def test_get_weather_city_too_long(self):
        """Test validation error when city name exceeds max length."""
        client = TestClient(app)
        long_city = "A" * 101

        response = client.get(f"/weather?city={long_city}")

        assert response.status_code == 422

    def test_get_weather_case_insensitive_cache(self, sample_weather_data):
        """Test cache is case-insensitive for city names."""
        with patch(
            "app.services.weather.WeatherService.get_weather",
            new_callable=AsyncMock,
            return_value=sample_weather_data,
        ):
            client = TestClient(app)

            # First request with lowercase
            response1 = client.get("/weather?city=london")
            assert response1.status_code == 200
            assert response1.json()["cached"] is False

            # Second request with uppercase - should hit cache
            response2 = client.get("/weather?city=LONDON")
            assert response2.status_code == 200
            assert response2.json()["cached"] is True


class TestAsyncWeatherEndpoint:
    """Async integration tests for the /weather endpoint."""

    @pytest.mark.asyncio
    async def test_async_get_weather(self, sample_weather_data):
        """Test weather endpoint with async client."""
        from app.models.weather import WeatherData

        # Create mock weather data for Paris
        mock_weather = WeatherData(
            city="Paris",
            country="FR",
            temperature=18.5,
            feels_like=17.0,
            humidity=60,
            pressure=1015,
            wind_speed=3.5,
            description="clear sky",
            icon="01d",
            timestamp=datetime.utcnow(),
        )

        with patch(
            "app.services.weather.WeatherService.get_weather",
            new_callable=AsyncMock,
            return_value=mock_weather,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get("/weather?city=Paris")

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["city"] == "Paris"
            assert data["cached"] is False

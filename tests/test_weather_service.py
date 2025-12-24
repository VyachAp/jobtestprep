"""Unit tests for the WeatherService."""

import pytest
import respx
from httpx import Response

from app.services.weather import (
    APIKeyError,
    CityNotFoundError,
    WeatherAPIError,
    WeatherService,
)


class TestWeatherService:
    """Tests for WeatherService class."""

    def test_init_without_api_key_raises(self, monkeypatch):
        """Test initialization fails without API key."""
        from app import config

        # Patch the settings object directly since it's already loaded
        monkeypatch.setattr(config.settings, "openweathermap_api_key", "")

        with pytest.raises(ValueError, match="API key is required"):
            WeatherService(api_key="")

    def test_init_with_api_key(self):
        """Test successful initialization with API key."""
        service = WeatherService(api_key="test_key")

        assert service._api_key == "test_key"

    @pytest.mark.asyncio
    async def test_get_weather_success(self, sample_weather_api_response):
        """Test successful weather data retrieval."""
        async with respx.mock(using="httpx") as respx_mock:
            respx_mock.get("https://api.openweathermap.org/data/2.5/weather").mock(
                return_value=Response(200, json=sample_weather_api_response)
            )

            service = WeatherService(api_key="test_key")
            weather_data = await service.get_weather("London")

            assert weather_data.city == "London"
            assert weather_data.country == "GB"
            assert weather_data.temperature == 12.5
            assert weather_data.humidity == 65
            assert weather_data.description == "broken clouds"

    @pytest.mark.asyncio
    async def test_get_weather_city_not_found(self):
        """Test 404 response raises CityNotFoundError."""
        async with respx.mock(using="httpx") as respx_mock:
            respx_mock.get("https://api.openweathermap.org/data/2.5/weather").mock(
                return_value=Response(
                    404, json={"cod": "404", "message": "city not found"}
                )
            )

            service = WeatherService(api_key="test_key")

            with pytest.raises(CityNotFoundError) as exc_info:
                await service.get_weather("NonexistentCity")

            assert exc_info.value.city == "NonexistentCity"
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_weather_invalid_api_key(self):
        """Test 401 response raises APIKeyError."""
        async with respx.mock(using="httpx") as respx_mock:
            respx_mock.get("https://api.openweathermap.org/data/2.5/weather").mock(
                return_value=Response(
                    401, json={"cod": 401, "message": "Invalid API key"}
                )
            )

            service = WeatherService(api_key="invalid_key")

            with pytest.raises(APIKeyError):
                await service.get_weather("London")

    @pytest.mark.asyncio
    async def test_get_weather_server_error(self):
        """Test 500 response raises WeatherAPIError."""
        async with respx.mock(using="httpx") as respx_mock:
            respx_mock.get("https://api.openweathermap.org/data/2.5/weather").mock(
                return_value=Response(500, text="Internal Server Error")
            )

            service = WeatherService(api_key="test_key")

            with pytest.raises(WeatherAPIError) as exc_info:
                await service.get_weather("London")

            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_get_weather_timeout(self):
        """Test timeout raises WeatherAPIError."""
        import httpx

        async with respx.mock(using="httpx") as respx_mock:
            respx_mock.get("https://api.openweathermap.org/data/2.5/weather").mock(
                side_effect=httpx.TimeoutException("Connection timed out")
            )

            service = WeatherService(api_key="test_key", timeout=1.0)

            with pytest.raises(WeatherAPIError) as exc_info:
                await service.get_weather("London")

            assert exc_info.value.status_code == 504
            assert "timed out" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_get_weather_network_error(self):
        """Test network error raises WeatherAPIError."""
        import httpx

        async with respx.mock(using="httpx") as respx_mock:
            respx_mock.get("https://api.openweathermap.org/data/2.5/weather").mock(
                side_effect=httpx.RequestError("Network unreachable")
            )

            service = WeatherService(api_key="test_key")

            with pytest.raises(WeatherAPIError) as exc_info:
                await service.get_weather("London")

            assert exc_info.value.status_code == 503

    def test_parse_response(self, sample_weather_api_response):
        """Test parsing of API response."""
        service = WeatherService(api_key="test_key")

        weather_data = service._parse_response(sample_weather_api_response)

        assert weather_data.city == "London"
        assert weather_data.country == "GB"
        assert weather_data.temperature == 12.5
        assert weather_data.feels_like == 11.2
        assert weather_data.humidity == 65
        assert weather_data.pressure == 1020
        assert weather_data.wind_speed == 4.1
        assert weather_data.description == "broken clouds"
        assert weather_data.icon == "04d"

    def test_parse_response_with_missing_fields(self):
        """Test parsing handles missing fields gracefully."""
        service = WeatherService(api_key="test_key")
        minimal_response = {
            "name": "TestCity",
            "main": {},
            "weather": [{}],
            "wind": {},
            "sys": {},
        }

        weather_data = service._parse_response(minimal_response)

        assert weather_data.city == "TestCity"
        assert weather_data.temperature == 0
        assert weather_data.description == ""

"""Weather service for fetching data from OpenWeatherMap API.

This module provides an async client for the OpenWeatherMap API
with proper error handling and data transformation.
"""

from datetime import datetime

import httpx

from app.config import settings
from app.models.weather import WeatherData


class WeatherAPIError(Exception):
    """Base exception for weather API errors."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class CityNotFoundError(WeatherAPIError):
    """Raised when the requested city is not found."""

    def __init__(self, city: str):
        super().__init__(f"City not found: {city}", status_code=404)
        self.city = city


class APIKeyError(WeatherAPIError):
    """Raised when the API key is invalid or missing."""

    def __init__(self):
        super().__init__("Invalid or missing API key", status_code=401)


class WeatherService:
    """Async client for OpenWeatherMap API.

    Fetches weather data using httpx with proper error handling
    and transforms responses into WeatherData models.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 10.0,
    ):
        self._api_key = api_key or settings.openweathermap_api_key
        self._base_url = base_url or settings.openweathermap_base_url
        self._timeout = timeout

        if not self._api_key:
            raise ValueError(
                "OpenWeatherMap API key is required. "
                "Set OPENWEATHERMAP_API_KEY environment variable."
            )

    async def get_weather(self, city: str) -> WeatherData:
        """Fetch current weather data for a city.

        Args:
            city: City name (e.g., "London", "New York, US").

        Returns:
            WeatherData object with current conditions.

        Raises:
            CityNotFoundError: If the city is not found.
            APIKeyError: If the API key is invalid.
            WeatherAPIError: For other API errors.
        """
        params = {
            "q": city,
            "appid": self._api_key,
            "units": "metric",  # Celsius
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(self._base_url, params=params)
            except httpx.TimeoutException:
                raise WeatherAPIError("Request timed out", status_code=504)
            except httpx.RequestError as e:
                raise WeatherAPIError(f"Network error: {str(e)}", status_code=503)

        return self._handle_response(response, city)

    def _handle_response(self, response: httpx.Response, city: str) -> WeatherData:
        """Handle API response and transform to WeatherData.

        Args:
            response: HTTP response from the API.
            city: Original city query for error messages.

        Returns:
            Parsed WeatherData object.

        Raises:
            CityNotFoundError: If city not found (404).
            APIKeyError: If API key is invalid (401).
            WeatherAPIError: For other API errors.
        """
        if response.status_code == 404:
            raise CityNotFoundError(city)

        if response.status_code == 401:
            raise APIKeyError()

        if response.status_code != 200:
            raise WeatherAPIError(
                f"API error: {response.text}",
                status_code=response.status_code,
            )

        return self._parse_response(response.json())

    def _parse_response(self, data: dict) -> WeatherData:
        """Parse OpenWeatherMap JSON response into WeatherData.

        Args:
            data: Raw JSON response from the API.

        Returns:
            Parsed WeatherData object.
        """
        main = data.get("main", {})
        weather = data.get("weather", [{}])[0]
        wind = data.get("wind", {})
        sys = data.get("sys", {})

        return WeatherData(
            city=data.get("name", "Unknown"),
            country=sys.get("country", ""),
            temperature=main.get("temp", 0),
            feels_like=main.get("feels_like", 0),
            humidity=main.get("humidity", 0),
            pressure=main.get("pressure", 0),
            wind_speed=wind.get("speed", 0),
            description=weather.get("description", ""),
            icon=weather.get("icon", ""),
            timestamp=datetime.utcnow(),
        )

"""Weather API router.

Handles weather data requests with caching, storage, event logging, and rate limiting.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.config import settings
from app.dependencies import (
    get_cache_service,
    get_event_logger,
    get_storage_service,
    get_weather_service,
)
from app.models.weather import WeatherResponse
from app.rate_limiter import limiter
from app.services.cache import CacheService
from app.services.event_logger import EventLogger
from app.services.storage import StorageService
from app.services.weather import WeatherService

router = APIRouter(tags=["weather"])


@router.get("/weather", response_model=WeatherResponse)
@limiter.limit(settings.rate_limit_weather)
async def get_weather(
    request: Request,
    city: str = Query(
        ...,
        min_length=1,
        max_length=100,
        description="City name (e.g., 'London', 'New York, US')",
        examples=["London", "Paris", "Tokyo"],
    ),
    cache_service: CacheService = Depends(get_cache_service),
    storage_service: StorageService = Depends(get_storage_service),
    event_logger: EventLogger = Depends(get_event_logger),
    weather_service: WeatherService | None = Depends(get_weather_service),
) -> WeatherResponse:
    """Get current weather data for a city.

    This endpoint fetches weather data from OpenWeatherMap API.
    Results are cached for 5 minutes to reduce API calls.

    - **city**: City name, optionally with country code (e.g., "London, UK")

    Returns weather data including temperature, humidity, wind speed, and conditions.
    """
    if weather_service is None:
        raise HTTPException(
            status_code=503,
            detail="Weather service not configured. Set OPENWEATHERMAP_API_KEY.",
        )

    # Check cache first
    cached_data = await cache_service.get(city)
    if cached_data:
        # Log the cached response
        await event_logger.log_weather_request(
            city=cached_data.city,
            timestamp=datetime.utcnow(),
            file_path="cached",
            cached=True,
        )
        return WeatherResponse(data=cached_data, cached=True, file_path="cached")

    # Fetch fresh data from API
    weather_data = await weather_service.get_weather(city)

    # Save to storage
    file_path = await storage_service.save_weather_data(weather_data)

    # Update cache
    await cache_service.set(city, weather_data)

    # Log the event
    await event_logger.log_weather_request(
        city=weather_data.city,
        timestamp=weather_data.timestamp,
        file_path=file_path,
        cached=False,
    )

    return WeatherResponse(data=weather_data, cached=False, file_path=file_path)


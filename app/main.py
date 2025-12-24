"""FastAPI Weather API Application.

A simple weather API service that fetches weather data from OpenWeatherMap,
with caching, local file storage, event logging, and rate limiting.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.dependencies import services
from app.exceptions import (
    api_key_error_handler,
    city_not_found_handler,
    weather_api_error_handler,
)
from app.rate_limiter import limiter
from app.routers import health_router, weather_router
from app.services.weather import APIKeyError, CityNotFoundError, WeatherAPIError


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown."""
    # Initialize services
    services.initialize()

    yield

    # Cleanup
    await services.cleanup()


app = FastAPI(
    title="Weather API",
    description="A simple weather API service with caching, local storage, and rate limiting",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure rate limiting
if settings.rate_limit_enabled:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Register exception handlers
app.add_exception_handler(CityNotFoundError, city_not_found_handler)
app.add_exception_handler(APIKeyError, api_key_error_handler)
app.add_exception_handler(WeatherAPIError, weather_api_error_handler)

# Include routers
app.include_router(weather_router)
app.include_router(health_router)

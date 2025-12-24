"""Custom exception handlers for the FastAPI application."""

from fastapi import Request
from fastapi.responses import JSONResponse

from app.services.weather import APIKeyError, CityNotFoundError, WeatherAPIError


async def weather_api_error_handler(
    request: Request, exc: WeatherAPIError
) -> JSONResponse:
    """Handle WeatherAPIError exceptions."""
    return JSONResponse(
        status_code=exc.status_code or 500,
        content={
            "error": exc.message,
            "type": type(exc).__name__,
        },
    )


async def city_not_found_handler(
    request: Request, exc: CityNotFoundError
) -> JSONResponse:
    """Handle CityNotFoundError exceptions."""
    return JSONResponse(
        status_code=404,
        content={
            "error": exc.message,
            "type": "CityNotFoundError",
            "city": exc.city,
        },
    )


async def api_key_error_handler(request: Request, exc: APIKeyError) -> JSONResponse:
    """Handle APIKeyError exceptions."""
    return JSONResponse(
        status_code=401,
        content={
            "error": exc.message,
            "type": "APIKeyError",
        },
    )

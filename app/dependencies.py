"""Application dependencies and service instances.

This module provides dependency injection for FastAPI routes,
managing the lifecycle of shared service instances.
"""

from app.services.cache import CacheService
from app.services.event_logger import EventLogger
from app.services.storage import StorageService
from app.services.weather import WeatherService


class ServiceContainer:
    """Container for application service instances."""

    def __init__(self):
        self.cache: CacheService | None = None
        self.storage: StorageService | None = None
        self.event_logger: EventLogger | None = None
        self.weather: WeatherService | None = None

    def initialize(self) -> None:
        """Initialize all services."""
        self.cache = CacheService()
        self.storage = StorageService()
        self.event_logger = EventLogger()

        try:
            self.weather = WeatherService()
        except ValueError as e:
            print(f"Warning: {e}")
            print("The API will return errors until a valid API key is configured.")
            self.weather = None

    async def cleanup(self) -> None:
        """Cleanup resources on shutdown."""
        if self.cache:
            await self.cache.clear()


# Global service container
services = ServiceContainer()


def get_cache_service() -> CacheService:
    """Dependency for cache service."""
    return services.cache


def get_storage_service() -> StorageService:
    """Dependency for storage service."""
    return services.storage


def get_event_logger() -> EventLogger:
    """Dependency for event logger."""
    return services.event_logger


def get_weather_service() -> WeatherService | None:
    """Dependency for weather service."""
    return services.weather


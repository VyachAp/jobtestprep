"""Storage abstraction for saving weather data.

This module provides a local file storage implementation that can be
easily swapped for S3 or other cloud storage solutions.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from app.config import settings
from app.models.weather import WeatherData


class BaseStorage(ABC):
    """Abstract base class for storage implementations."""

    @abstractmethod
    async def save(self, data: WeatherData) -> str:
        """Save weather data and return the storage path/URL."""
        pass

    @abstractmethod
    async def load(self, path: str) -> WeatherData | None:
        """Load weather data from the given path."""
        pass


class LocalFileStorage(BaseStorage):
    """Local file storage implementation.

    Saves weather data as JSON files in the configured data directory.
    Can be easily replaced with S3Storage for cloud deployment.
    """

    def __init__(self, base_path: Path | None = None):
        self.base_path = base_path or settings.data_dir
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _generate_filename(self, city: str, timestamp: datetime) -> str:
        """Generate filename in format: {city}_{timestamp}.json"""
        sanitized_city = city.lower().replace(" ", "_")
        ts_str = timestamp.strftime("%Y%m%d_%H%M%S")
        return f"{sanitized_city}_{ts_str}.json"

    async def save(self, data: WeatherData) -> str:
        """Save weather data to a JSON file.

        Args:
            data: Weather data to save.

        Returns:
            Path to the saved file.
        """
        filename = self._generate_filename(data.city, data.timestamp)
        file_path = self.base_path / filename

        content = data.model_dump_json(indent=2)
        file_path.write_text(content, encoding="utf-8")

        return str(file_path)

    async def load(self, path: str) -> WeatherData | None:
        """Load weather data from a JSON file.

        Args:
            path: Path to the JSON file.

        Returns:
            Weather data or None if file doesn't exist.
        """
        file_path = Path(path)
        if not file_path.exists():
            return None

        content = file_path.read_text(encoding="utf-8")
        return WeatherData.model_validate_json(content)


class StorageService:
    """High-level storage service that wraps the storage implementation.

    This service provides the public API for storage operations and
    makes it easy to swap storage backends.
    """

    def __init__(self, storage: BaseStorage | None = None):
        self._storage = storage or LocalFileStorage()

    async def save_weather_data(self, data: WeatherData) -> str:
        """Save weather data and return the storage path."""
        return await self._storage.save(data)

    async def load_weather_data(self, path: str) -> WeatherData | None:
        """Load weather data from the given path."""
        return await self._storage.load(path)

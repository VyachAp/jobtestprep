"""In-memory cache with TTL for weather data.

This module provides a simple in-memory cache implementation with
time-based expiration. Can be replaced with Redis for production.
"""

from datetime import datetime, timedelta

from app.config import settings
from app.models.weather import WeatherData


class CacheEntry:
    """A cache entry with expiration tracking."""

    def __init__(self, data: WeatherData, ttl_seconds: int):
        self.data = data
        self.created_at = datetime.utcnow()
        self.expires_at = self.created_at + timedelta(seconds=ttl_seconds)

    def is_expired(self) -> bool:
        """Check if this cache entry has expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def age_seconds(self) -> float:
        """Get the age of this entry in seconds."""
        return (datetime.utcnow() - self.created_at).total_seconds()


class CacheService:
    """In-memory cache service for weather data.

    Provides a simple key-value cache with TTL (time-to-live) support.
    Can be replaced with Redis or Memcached for distributed caching.
    """

    def __init__(self, ttl_seconds: int | None = None):
        self._cache: dict[str, CacheEntry] = {}
        self._ttl_seconds = ttl_seconds or settings.cache_ttl_seconds

    def _normalize_key(self, city: str) -> str:
        """Normalize city name for use as cache key."""
        return city.lower().strip()

    async def get(self, city: str) -> WeatherData | None:
        """Get cached weather data for a city.

        Args:
            city: The city to look up.

        Returns:
            Cached weather data if available and not expired, None otherwise.
        """
        key = self._normalize_key(city)
        entry = self._cache.get(key)

        if entry is None:
            return None

        if entry.is_expired():
            del self._cache[key]
            return None

        return entry.data

    async def set(self, city: str, data: WeatherData) -> None:
        """Cache weather data for a city.

        Args:
            city: The city to cache data for.
            data: The weather data to cache.
        """
        key = self._normalize_key(city)
        self._cache[key] = CacheEntry(data, self._ttl_seconds)

    async def invalidate(self, city: str) -> bool:
        """Remove cached data for a city.

        Args:
            city: The city to invalidate.

        Returns:
            True if an entry was removed, False otherwise.
        """
        key = self._normalize_key(city)
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    async def clear(self) -> int:
        """Clear all cached data.

        Returns:
            Number of entries cleared.
        """
        count = len(self._cache)
        self._cache.clear()
        return count

    def get_stats(self) -> dict:
        """Get cache statistics."""
        now = datetime.utcnow()
        active_entries = {
            k: v for k, v in self._cache.items() if not v.is_expired()
        }

        return {
            "total_entries": len(self._cache),
            "active_entries": len(active_entries),
            "ttl_seconds": self._ttl_seconds,
        }


"""Unit tests for the CacheService."""
import pytest

from app.services.cache import CacheEntry, CacheService


class TestCacheEntry:
    """Tests for CacheEntry class."""

    def test_cache_entry_creation(self, sample_weather_data):
        """Test cache entry is created with correct expiration."""
        entry = CacheEntry(sample_weather_data, ttl_seconds=300)

        assert entry.data == sample_weather_data
        assert entry.created_at is not None
        assert entry.expires_at > entry.created_at

    def test_cache_entry_not_expired(self, sample_weather_data):
        """Test cache entry is not expired immediately after creation."""
        entry = CacheEntry(sample_weather_data, ttl_seconds=300)

        assert not entry.is_expired()

    def test_cache_entry_expired(self, sample_weather_data):
        """Test cache entry expires after TTL."""
        entry = CacheEntry(sample_weather_data, ttl_seconds=0)

        # Entry should be expired immediately with 0 TTL
        assert entry.is_expired()

    def test_cache_entry_age_seconds(self, sample_weather_data):
        """Test age calculation for cache entry."""
        entry = CacheEntry(sample_weather_data, ttl_seconds=300)

        age = entry.age_seconds
        assert age >= 0
        assert age < 1  # Should be less than 1 second after creation


class TestCacheService:
    """Tests for CacheService class."""

    @pytest.mark.asyncio
    async def test_get_miss(self, cache_service):
        """Test cache miss returns None."""
        result = await cache_service.get("nonexistent_city")

        assert result is None

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache_service, sample_weather_data):
        """Test setting and retrieving cached data."""
        await cache_service.set("London", sample_weather_data)

        result = await cache_service.get("London")

        assert result is not None
        assert result.city == "London"
        assert result.temperature == sample_weather_data.temperature

    @pytest.mark.asyncio
    async def test_key_normalization(self, cache_service, sample_weather_data):
        """Test cache key normalization (case insensitive)."""
        await cache_service.set("London", sample_weather_data)

        # Should find with different case
        result = await cache_service.get("LONDON")
        assert result is not None

        result = await cache_service.get("  london  ")
        assert result is not None

    @pytest.mark.asyncio
    async def test_expired_entry_returns_none(self, sample_weather_data):
        """Test expired entries return None and are removed."""
        import time

        cache = CacheService(ttl_seconds=1)  # 1 second expiration
        await cache.set("London", sample_weather_data)

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired
        result = await cache.get("London")

        assert result is None

    @pytest.mark.asyncio
    async def test_invalidate_existing(self, cache_service, sample_weather_data):
        """Test invalidating an existing cache entry."""
        await cache_service.set("London", sample_weather_data)

        removed = await cache_service.invalidate("London")

        assert removed is True
        assert await cache_service.get("London") is None

    @pytest.mark.asyncio
    async def test_invalidate_nonexistent(self, cache_service):
        """Test invalidating a nonexistent entry returns False."""
        removed = await cache_service.invalidate("nonexistent")

        assert removed is False

    @pytest.mark.asyncio
    async def test_clear(self, cache_service, sample_weather_data):
        """Test clearing all cache entries."""
        await cache_service.set("London", sample_weather_data)
        await cache_service.set("Paris", sample_weather_data)

        count = await cache_service.clear()

        assert count == 2
        assert await cache_service.get("London") is None
        assert await cache_service.get("Paris") is None

    def test_get_stats(self, cache_service):
        """Test cache statistics retrieval."""
        stats = cache_service.get_stats()

        assert "total_entries" in stats
        assert "active_entries" in stats
        assert "ttl_seconds" in stats
        assert stats["ttl_seconds"] == 60

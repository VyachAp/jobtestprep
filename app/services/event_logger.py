"""Event logging abstraction for tracking weather API requests.

This module provides a SQLite-based logging implementation that can be
easily swapped for DynamoDB or other database solutions.
"""

import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

import aiosqlite

from app.config import settings


class BaseEventLogger(ABC):
    """Abstract base class for event logging implementations."""

    @abstractmethod
    async def log_event(
        self, city: str, timestamp: datetime, file_path: str, cached: bool = False
    ) -> None:
        """Log a weather request event."""
        pass

    @abstractmethod
    async def get_events(self, city: str | None = None, limit: int = 100) -> list[dict]:
        """Retrieve logged events, optionally filtered by city."""
        pass


class SQLiteEventLogger(BaseEventLogger):
    """SQLite-based event logger.

    Logs weather request events to a SQLite database.
    Can be easily replaced with DynamoDBEventLogger for cloud deployment.
    """

    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or (settings.logs_dir / "events.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """Initialize the database schema if not already done."""
        if self._initialized:
            return

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS weather_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    city TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    cached BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_city ON weather_events(city)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON weather_events(timestamp)
            """)
            await db.commit()

        self._initialized = True

    async def log_event(
        self, city: str, timestamp: datetime, file_path: str, cached: bool = False
    ) -> None:
        """Log a weather request event.

        Args:
            city: The requested city.
            timestamp: Timestamp of the request.
            file_path: Path where the data was saved.
            cached: Whether the response was served from cache.
        """
        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO weather_events (city, timestamp, file_path, cached)
                VALUES (?, ?, ?, ?)
                """,
                (city, timestamp.isoformat(), file_path, cached),
            )
            await db.commit()

    async def get_events(self, city: str | None = None, limit: int = 100) -> list[dict]:
        """Retrieve logged events.

        Args:
            city: Optional city filter.
            limit: Maximum number of events to return.

        Returns:
            List of event dictionaries.
        """
        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            if city:
                cursor = await db.execute(
                    """
                    SELECT * FROM weather_events
                    WHERE city = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (city.lower(), limit),
                )
            else:
                cursor = await db.execute(
                    """
                    SELECT * FROM weather_events
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                )

            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


class EventLogger:
    """High-level event logging service.

    Wraps the underlying logger implementation and provides
    the public API for event logging operations.
    """

    def __init__(self, logger: BaseEventLogger | None = None):
        self._logger = logger or SQLiteEventLogger()

    async def log_weather_request(
        self, city: str, timestamp: datetime, file_path: str, cached: bool = False
    ) -> None:
        """Log a weather request event."""
        await self._logger.log_event(city, timestamp, file_path, cached)

    async def get_request_history(
        self, city: str | None = None, limit: int = 100
    ) -> list[dict]:
        """Get weather request history."""
        return await self._logger.get_events(city, limit)

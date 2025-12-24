"""Health and monitoring router.

Provides health checks and event history endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.config import settings
from app.dependencies import get_cache_service, get_event_logger
from app.rate_limiter import limiter
from app.services.cache import CacheService
from app.services.event_logger import EventLogger

router = APIRouter(tags=["monitoring"])


@router.get("/health")
@limiter.limit(settings.rate_limit_default)
async def health_check(
    request: Request,
    cache_service: CacheService = Depends(get_cache_service),
) -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "weather-api",
        "cache_stats": cache_service.get_stats() if cache_service else None,
    }


@router.get("/events")
@limiter.limit(settings.rate_limit_default)
async def get_events(
    request: Request,
    city: str | None = Query(None, description="Filter events by city"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum events to return"),
    event_logger: EventLogger = Depends(get_event_logger),
) -> dict:
    """Get weather request event history."""
    if event_logger is None:
        raise HTTPException(status_code=503, detail="Event logger not initialized")

    events = await event_logger.get_request_history(city=city, limit=limit)
    return {"events": events, "count": len(events)}


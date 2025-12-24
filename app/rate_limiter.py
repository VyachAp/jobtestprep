"""Rate limiting configuration for the Weather API.

This module provides rate limiting functionality to prevent API abuse.
Uses slowapi which is built on top of the limits library.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings


def get_client_identifier(request) -> str:
    """Extract client identifier from request.

    Uses X-Forwarded-For header if present (for proxied requests),
    otherwise falls back to remote address.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take the first IP in the chain (original client)
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


# Create the limiter instance
limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=[settings.rate_limit_default],
    storage_uri=settings.rate_limit_storage_uri,
    strategy="fixed-window",
)

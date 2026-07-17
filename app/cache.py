"""Redis caching layer with graceful fallback."""

import json
import logging

from app.config import settings

logger = logging.getLogger(__name__)

_redis_client = None
_available = False


def init_redis() -> bool:
    """Initialize Redis connection. Returns True if connected."""
    global _redis_client, _available

    try:
        import redis

        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        _redis_client.ping()
        _available = True
        logger.info("Redis connected: %s", settings.redis_url)
        return True
    except Exception as e:
        logger.warning("Redis unavailable, caching disabled: %s", e)
        _available = False
        return False


def get_cached(key: str) -> dict | None:
    """Get value from cache. Returns None if miss or unavailable."""
    if not _available or _redis_client is None:
        return None

    try:
        data = _redis_client.get(key)
        if data:
            return json.loads(data)
    except Exception:
        pass
    return None


def set_cached(key: str, value: dict, ttl: int | None = None) -> bool:
    """Set value in cache. Returns True if successful."""
    if not _available or _redis_client is None:
        return False

    try:
        ttl = ttl or settings.cache_ttl_seconds
        _redis_client.setex(key, ttl, json.dumps(value))
        return True
    except Exception:
        return False


def is_available() -> bool:
    return _available

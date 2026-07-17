"""In-memory rate limiter per API key."""

import time
from collections import defaultdict

from app.config import settings

_buckets: dict[str, list[float]] = defaultdict(list)


def is_rate_limited(api_key: str) -> bool:
    """Check if the API key has exceeded the rate limit."""
    now = time.time()
    window = 60  # 1 minute

    # Clean old entries
    _buckets[api_key] = [
        t for t in _buckets[api_key] if now - t < window
    ]

    if len(_buckets[api_key]) >= settings.rate_limit_per_minute:
        return True

    _buckets[api_key].append(now)
    return False


def get_remaining(api_key: str) -> int:
    """Get remaining requests in current window."""
    now = time.time()
    window = 60
    recent = [t for t in _buckets[api_key] if now - t < window]
    return max(0, settings.rate_limit_per_minute - len(recent))

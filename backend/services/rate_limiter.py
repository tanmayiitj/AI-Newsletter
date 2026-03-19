"""In-memory sliding-window rate limiter keyed by client IP."""

import time
from collections import defaultdict

from backend.config.settings import settings


# Stores timestamps of requests per IP: { ip: [ts1, ts2, ...] }
_requests: dict[str, list[float]] = defaultdict(list)


async def check_rate_limit(ip: str) -> bool:
    """Check whether a request from *ip* is within the rate limit.

    Uses a sliding-window algorithm: only timestamps within the current
    window are kept.  Expired entries are cleaned up on each call.

    Args:
        ip: Client IP address string.

    Returns:
        True if the request is allowed, False if the limit is exceeded.
    """
    now = time.monotonic()
    window = settings.rate_limit_window_seconds
    max_requests = settings.rate_limit_max_requests

    # Prune expired timestamps for this IP
    timestamps = _requests[ip]
    _requests[ip] = [ts for ts in timestamps if now - ts < window]

    if len(_requests[ip]) >= max_requests:
        return False

    _requests[ip].append(now)
    return True


def reset() -> None:
    """Clear all rate-limit state.  Intended for testing only."""
    _requests.clear()

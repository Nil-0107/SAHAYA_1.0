"""Small process-local abuse guard for authentication and expensive AI calls."""

from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock
from time import monotonic


class RateLimitExceeded(RuntimeError):
    pass


_events: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()


def clear_rate_limits() -> None:
    with _lock:
        _events.clear()


def enforce_rate_limit(key: str, *, limit: int, window_seconds: int) -> None:
    now = monotonic()
    cutoff = now - window_seconds
    with _lock:
        events = _events[key]
        while events and events[0] < cutoff:
            events.popleft()
        if len(events) >= limit:
            raise RateLimitExceeded("Too many requests")
        events.append(now)

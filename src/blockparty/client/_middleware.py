"""Client middleware: caching, retry with backoff, and error parsing.

These are standalone utilities used by both the async and sync clients
to handle cross-cutting concerns without duplicating logic.
"""

from __future__ import annotations

import hashlib
import json
import random
import time
from typing import Any

# ---------------------------------------------------------------------------
# Response cache
# ---------------------------------------------------------------------------


class ResponseCache:
    """Simple TTL cache keyed by request parameters.

    Thread-safe for reads (dict lookups are atomic in CPython), but writes
    are not synchronized — acceptable for a best-effort cache.
    """

    __slots__ = ("_store", "_ttl")

    def __init__(self, ttl: int = 30) -> None:
        self._store: dict[str, tuple[float, Any]] = {}
        self._ttl = ttl

    @property
    def ttl(self) -> int:
        return self._ttl

    @staticmethod
    def make_key(params: dict[str, str]) -> str:
        """Create a deterministic cache key from request parameters."""
        canonical = json.dumps(params, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()

    def get(self, key: str) -> Any | None:
        """Return cached value if present and not expired, else None."""
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() > expires_at:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        """Store a value with the configured TTL."""
        if self._ttl <= 0:
            return
        self._store[key] = (time.monotonic() + self._ttl, value)

    def clear(self) -> None:
        self._store.clear()


# ---------------------------------------------------------------------------
# Retry / backoff configuration
# ---------------------------------------------------------------------------


class RetryConfig:
    """Configuration for exponential backoff with jitter."""

    __slots__ = (
        "max_retries",
        "backoff_base",
        "backoff_multiplier",
        "max_backoff",
        "jitter_factor",
        "retryable_statuses",
    )

    def __init__(
        self,
        max_retries: int = 3,
        backoff_base: float = 1.0,
        backoff_multiplier: float = 2.0,
        max_backoff: float = 30.0,
        jitter_factor: float = 0.25,
    ) -> None:
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.backoff_multiplier = backoff_multiplier
        self.max_backoff = max_backoff
        self.jitter_factor = jitter_factor
        self.retryable_statuses = {429, 500, 502, 503, 504}

    def delay(self, attempt: int) -> float:
        """Calculate the delay for a given retry attempt (0-indexed)."""
        base = self.backoff_base * (self.backoff_multiplier**attempt)
        base = min(base, self.max_backoff)
        jitter = base * self.jitter_factor
        return base + random.uniform(-jitter, jitter)

    def should_retry_status(self, status_code: int) -> bool:
        return status_code in self.retryable_statuses

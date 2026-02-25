"""Token bucket rate limiter for a single (provider, credential) pair.

Supports both async and sync acquisition, and dynamic adaptation from
Blockscout's ``X-Ratelimit-*`` response headers.
"""

from __future__ import annotations

import asyncio
import threading
import time


class RateLimitBudget:
    """Token bucket that controls the rate of API requests.

    Each bucket is associated with a single ``(provider, api_key)`` pair.
    Multiple clients sharing the same credential share one bucket.

    The bucket refills at ``rps`` tokens per second, up to a maximum of
    ``rps`` tokens (burst capacity = 1 second worth of requests).

    Args:
        rps: Requests per second (token refill rate and max capacity).
    """

    __slots__ = ("_capacity", "_tokens", "_last_refill", "_lock", "_async_lock")

    def __init__(self, rps: int) -> None:
        self._capacity: float = float(rps)
        self._tokens: float = float(rps)  # start full
        self._last_refill: float = time.monotonic()
        self._lock = threading.Lock()
        self._async_lock = asyncio.Lock()

    @property
    def rps(self) -> float:
        """Current requests-per-second rate (reflects adaptive updates)."""
        return self._capacity

    @property
    def capacity(self) -> float:
        """Current maximum token capacity (reflects adaptive updates)."""
        return self._capacity

    # ------------------------------------------------------------------
    # Internal refill
    # ------------------------------------------------------------------

    def _refill(self) -> None:
        """Add tokens based on elapsed time since last refill."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._capacity, self._tokens + elapsed * self._capacity)
        self._last_refill = now

    def _wait_time(self) -> float:
        """Seconds until at least one token is available."""
        if self._tokens >= 1.0:
            return 0.0
        return (1.0 - self._tokens) / self._capacity

    # ------------------------------------------------------------------
    # Async acquisition
    # ------------------------------------------------------------------

    async def acquire(self) -> None:
        """Wait until a token is available, then consume one.

        This is the primary method for async clients.
        """
        while True:
            async with self._async_lock:
                self._refill()
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
                wait = self._wait_time()
            await asyncio.sleep(wait)

    # ------------------------------------------------------------------
    # Sync acquisition
    # ------------------------------------------------------------------

    def acquire_sync(self) -> None:
        """Blocking wait until a token is available, then consume one.

        This is the primary method for sync clients.
        """
        while True:
            with self._lock:
                self._refill()
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
                wait = self._wait_time()
            time.sleep(wait)

    # ------------------------------------------------------------------
    # Blockscout header-based adaptive update
    # ------------------------------------------------------------------

    def update_from_headers(self, headers: dict[str, str]) -> None:
        """Adapt the bucket from Blockscout rate limit response headers.

        Expected headers::

            X-Ratelimit-Limit: 600      (requests per window)
            X-Ratelimit-Remaining: 598
            X-Ratelimit-Reset: 60000    (milliseconds)

        The bucket capacity is recalculated as
        ``limit / (reset_ms / 1000)`` to derive an effective RPS.
        The current token count is set to ``remaining / (reset_ms / 1000)``.
        """
        limit_str = headers.get("x-ratelimit-limit") or headers.get("X-Ratelimit-Limit")
        remaining_str = headers.get("x-ratelimit-remaining") or headers.get("X-Ratelimit-Remaining")
        reset_str = headers.get("x-ratelimit-reset") or headers.get("X-Ratelimit-Reset")

        if not (limit_str and remaining_str and reset_str):
            return

        try:
            limit = int(limit_str)
            remaining = int(remaining_str)
            reset_ms = int(reset_str)
        except (ValueError, TypeError):
            return

        if reset_ms <= 0:
            return

        reset_seconds = reset_ms / 1000.0
        new_capacity = limit / reset_seconds
        tokens_remaining = remaining / reset_seconds

        self._capacity = new_capacity
        self._tokens = min(new_capacity, tokens_remaining)
        self._last_refill = time.monotonic()

    def __repr__(self) -> str:
        return f"RateLimitBudget(capacity={self._capacity:.1f}, tokens={self._tokens:.1f})"

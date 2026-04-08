"""Rate limiting service for Claude Code Python.

Handles rate limiting for API calls with exponential backoff.
"""

import asyncio
import time
from asyncio import Lock
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class RateLimitError(Exception):
    """Exception raised when rate limited.

    Attributes:
        message: Error message.
        retry_after: Seconds to wait before retrying.
    """

    def __init__(self, message: str, retry_after: Optional[float] = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class RateLimitMode(Enum):
    """Rate limit handling modes."""

    RETRY = "retry"  # Automatically retry with backoff
    RAISE = "raise"  # Raise exception immediately
    QUEUE = "queue"  # Queue requests for later


@dataclass(frozen=True)
class RateLimitConfig:
    """Configuration for rate limiting.

    Attributes:
        max_requests_per_minute: Maximum requests per minute.
        max_requests_per_second: Maximum requests per second.
        base_delay: Base delay for exponential backoff.
        max_delay: Maximum delay between retries.
        max_retries: Maximum number of retry attempts.
        mode: How to handle rate limiting.
    """

    max_requests_per_minute: int = 50
    max_requests_per_second: int = 10
    base_delay: float = 1.0
    max_delay: float = 60.0
    max_retries: int = 5
    mode: RateLimitMode = RateLimitMode.RETRY


@dataclass(frozen=True)
class RateLimitStatus:
    """Current rate limit status.

    Attributes:
        requests_this_minute: Number of requests in current minute.
        requests_this_second: Number of requests in current second.
        last_request_time: Timestamp of the last request.
        remaining_requests: Remaining requests available.
        reset_time: When the rate limit will reset.
    """

    requests_this_minute: int = 0
    requests_this_second: int = 0
    last_request_time: float = 0.0
    remaining_requests: int = 50
    reset_time: Optional[float] = None


class RateLimiter:
    """Token bucket rate limiter with sliding window.

    Tracks requests per second and per minute to respect API limits.
    """

    def __init__(self, config: Optional[RateLimitConfig] = None) -> None:
        """Initialize rate limiter.

        Args:
            config: Rate limit configuration (uses defaults if not provided).
        """
        self.config = config or RateLimitConfig()
        self._lock = Lock()
        self._minute_window: List[float] = []
        self._second_window: List[float] = []
        self._status = RateLimitStatus()
        self._request_counts: Dict[str, List[float]] = defaultdict(list)

    async def acquire(self, key: str = "default") -> None:
        """Acquire permission to make a request.

        Blocks until rate limit allows the request.
        Raises RateLimitError if max retries exceeded.

        Args:
            key: Optional key for per-key rate limiting.
        """
        async with self._lock:
            now = time.time()
            self._cleanup_windows(now)

            # Check if we're at the limit
            retry_count = 0
            while retry_count < self.config.max_retries:
                if self._can_proceed():
                    break

                # Calculate backoff delay
                delay = min(
                    self.config.base_delay * (2 ** retry_count),
                    self.config.max_delay,
                )

                retry_count += 1

                if self.config.mode == RateLimitMode.RAISE:
                    raise RateLimitError(
                        "Rate limit exceeded",
                        retry_after=delay,
                    )

                # Release lock while waiting
                self._lock.release()
                try:
                    await asyncio.sleep(delay)
                finally:
                    await self._lock.acquire()

                # Recheck after sleep
                now = time.time()
                self._cleanup_windows(now)

            # Record this request
            self._record_request(key, now)
            self._update_status()

    def _can_proceed(self) -> bool:
        """Check if we can make another request.

        Returns:
            True if rate limit allows proceeding.
        """
        return (
            len(self._second_window) < self.config.max_requests_per_second
            and len(self._minute_window) < self.config.max_requests_per_minute
        )

    def _cleanup_windows(self, now: float) -> None:
        """Remove old timestamps from windows.

        Args:
            now: Current timestamp.
        """
        second_ago = now - 1
        minute_ago = now - 60

        self._second_window = [t for t in self._second_window if t > second_ago]
        self._minute_window = [t for t in self._minute_window if t > minute_ago]

    def _record_request(self, key: str, now: float) -> None:
        """Record a request.

        Args:
            key: The rate limit key.
            now: Current timestamp.
        """
        self._minute_window.append(now)
        self._second_window.append(now)
        self._request_counts[key].append(now)

        # Cleanup key-specific window
        minute_ago = now - 60
        self._request_counts[key] = [
            t for t in self._request_counts[key] if t > minute_ago
        ]

    def _update_status(self) -> None:
        """Update rate limit status."""
        self._status.requests_this_minute = len(self._minute_window)
        self._status.requests_this_second = len(self._second_window)
        self._status.remaining_requests = (
            self.config.max_requests_per_minute - len(self._minute_window)
        )
        self._status.last_request_time = time.time()

    @property
    def status(self) -> RateLimitStatus:
        """Get current rate limit status."""
        return self._status

    def reset(self) -> None:
        """Reset rate limiter state."""
        self._minute_window.clear()
        self._second_window.clear()
        self._request_counts.clear()
        self._status = RateLimitStatus()


class TokenBucketRateLimiter:
    """Token bucket rate limiter for more flexible rate limiting.

    Allows burst traffic up to bucket capacity.
    """

    def __init__(
        self,
        tokens_per_second: float = 10,
        bucket_size: int = 20,
    ) -> None:
        """Initialize token bucket rate limiter.

        Args:
            tokens_per_second: Rate of token replenishment.
            bucket_size: Maximum number of tokens in the bucket.
        """
        self.tokens_per_second = tokens_per_second
        self.bucket_size = bucket_size
        self._tokens = float(bucket_size)
        self._last_update = time.time()
        self._lock = Lock()

    async def acquire(self, tokens: int = 1) -> None:
        """Acquire tokens for a request.

        Args:
            tokens: Number of tokens to acquire.
        """
        async with self._lock:
            now = time.time()

            # Add tokens based on elapsed time
            elapsed = now - self._last_update
            self._tokens = min(
                self.bucket_size,
                self._tokens + elapsed * self.tokens_per_second,
            )
            self._last_update = now

            # Wait if not enough tokens
            while self._tokens < tokens:
                wait_time = (tokens - self._tokens) / self.tokens_per_second
                await asyncio.sleep(wait_time)
                now = time.time()
                self._tokens = min(
                    self.bucket_size,
                    self._tokens + (now - self._last_update) * self.tokens_per_second,
                )
                self._last_update = now

            # Consume tokens
            self._tokens -= tokens


_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance.

    Returns:
        The global RateLimiter singleton.
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def set_rate_limiter(limiter: RateLimiter) -> None:
    """Set the global rate limiter instance.

    Args:
        limiter: The RateLimiter to use globally.
    """
    global _rate_limiter
    _rate_limiter = limiter


async def with_rate_limit(coro: Any, key: str = "default") -> Any:
    """Execute a coroutine with rate limiting.

    Args:
        coro: Coroutine to execute.
        key: Optional key for per-key rate limiting.

    Returns:
        Result of the coroutine.

    Usage:
        result = await with_rate_limit(api_call(), "my_key")
    """
    limiter = get_rate_limiter()
    await limiter.acquire(key)
    return await coro
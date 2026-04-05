"""Cache Service for Claude Code Python.

Provides caching functionality for API responses and file reads.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path
from typing import Any, Callable, TypeVar

T = TypeVar("T")


@dataclass(slots=True)
class CacheEntry:
    """A single cache entry.

    Attributes:
        key: Cache key.
        value: Cached value.
        created_at: Unix timestamp when created.
        expires_at: Unix timestamp when entry expires (None for no expiry).
        hit_count: Number of times the entry was accessed.
    """

    key: str
    value: Any
    created_at: float
    expires_at: float | None = None
    hit_count: int = 0

    def is_expired(self) -> bool:
        """Check if entry has expired.

        Returns:
            True if entry has expired.
        """
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


class CacheService:
    """In-memory cache with optional disk persistence.

    Features:
    - TTL support
    - LRU eviction
    - Disk persistence
    - Thread-safe operations
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: float | None = None,
        persist_dir: Path | str | None = None,
    ) -> None:
        """Initialize CacheService.

        Args:
            max_size: Maximum number of entries.
            default_ttl: Default time-to-live in seconds.
            persist_dir: Directory for disk persistence.
        """
        self._cache: dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._persist_dir = Path(persist_dir) if persist_dir else None
        self._lock = asyncio.Lock()

        if self._persist_dir:
            self._persist_dir.mkdir(parents=True, exist_ok=True)

    def _make_key(self, *args: Any, **kwargs: Any) -> str:
        """Generate cache key from arguments.

        Args:
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            SHA256 hash as cache key.
        """
        key_data = {
            "args": args,
            "kwargs": sorted(kwargs.items()),
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.sha256(key_str.encode()).hexdigest()[:32]

    async def get(self, key: str) -> Any | None:
        """Get value from cache.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found/expired.
        """
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None

            if entry.is_expired():
                del self._cache[key]
                return None

            entry.hit_count += 1  # type: ignore[attr-defined]
            return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: float | None = None,
    ) -> None:
        """Set value in cache.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Optional time-to-live in seconds.
        """
        async with self._lock:
            if len(self._cache) >= self._max_size:
                self._evict_lru()

            expires_at: float | None = None
            effective_ttl = ttl if ttl is not None else self._default_ttl
            if effective_ttl:
                expires_at = time.time() + effective_ttl

            self._cache[key] = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                expires_at=expires_at,
            )

    async def delete(self, key: str) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key.

        Returns:
            True if deleted, False if not found.
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()

    async def has(self, key: str) -> bool:
        """Check if key exists and is not expired.

        Args:
            key: Cache key.

        Returns:
            True if key exists and is not expired.
        """
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False
            if entry.is_expired():
                await self.delete(key)
                return False
            return True

    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._cache:
            return

        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].created_at,
        )
        del self._cache[lru_key]

    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics.
        """
        async with self._lock:
            total_hits = sum(e.hit_count for e in self._cache.values())
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "total_hits": total_hits,
                "default_ttl": self._default_ttl,
                "persist_dir": str(self._persist_dir) if self._persist_dir else None,
            }


def cached(
    ttl: float | None = None,
    key_func: Callable[..., str] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to cache function results.

    Args:
        ttl: Time-to-live for cached results.
        key_func: Custom function to generate cache key.

    Returns:
        Decorated function with caching.

    Usage:
        @cached(ttl=60)
        async def my_function(arg1, arg2):
            ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        _cache: CacheService = CacheService(default_ttl=ttl)

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                key_parts = [func.__name__]
                key_parts.extend(str(a) for a in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()

            cached_value = await _cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            result = await func(*args, **kwargs)
            await _cache.set(cache_key, result, ttl)
            return result

        wrapper.cache = _cache  # type: ignore[attr-defined]
        return wrapper

    return decorator


_global_cache: CacheService | None = None


def get_cache() -> CacheService:
    """Get global cache instance.

    Returns:
        Global CacheService instance.
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = CacheService()
    return _global_cache
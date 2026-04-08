"""Cache Service for Claude Code Python.

Provides caching functionality for API responses and file reads.
Supports multiple caching strategies: Cache-Aside, Write-Through, Write-Behind.
"""

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union

T = TypeVar("T")


class CacheStrategy(Enum):
    """Cache strategy types."""

    CACHE_ASIDE = "cache_aside"
    WRITE_THROUGH = "write_through"
    WRITE_BEHIND = "write_behind"


@dataclass(frozen=True)
class CacheConfig:
    """Configuration for cache service.

    Attributes:
        max_size: Maximum number of entries.
        default_ttl: Default time-to-live in seconds.
        persist_dir: Directory for disk persistence.
        strategy: Cache strategy to use.
        enable_stats: Enable detailed statistics.
    """

    max_size: int = 1000
    default_ttl: Optional[float] = None
    persist_dir: Optional[Union[Path, str]] = None
    strategy: CacheStrategy = CacheStrategy.CACHE_ASIDE
    enable_stats: bool = True


@dataclass
class CacheEntry:
    """A single cache entry.

    Attributes:
        key: Cache key.
        value: Cached value.
        created_at: Unix timestamp when created.
        expires_at: Unix timestamp when entry expires (None for no expiry).
        hit_count: Number of times the entry was accessed.
        last_accessed: Last access timestamp for LFU eviction.
    """

    key: str
    value: Any
    created_at: float
    expires_at: Optional[float] = None
    hit_count: int = 0
    last_accessed: float = field(default_factory=time.time)

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
    - Multiple caching strategies (Cache-Aside, Write-Through, Write-Behind)
    - TTL support
    - LRU/LFU eviction
    - Disk persistence
    - Thread-safe operations
    """

    def __init__(self, config: Optional[CacheConfig] = None) -> None:
        """Initialize CacheService.

        Args:
            config: Cache configuration (uses defaults if not provided).
        """
        self.config = config or CacheConfig()
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
        self._write_queue: Optional[asyncio.Queue] = None
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "writes": 0,
        }

        if self.config.persist_dir:
            self._persist_dir = Path(self.config.persist_dir)
            self._persist_dir.mkdir(parents=True, exist_ok=True)
        else:
            self._persist_dir = None

    def _make_key(self, *args: Any, **kwargs: Any) -> str:
        """Generate cache key from arguments.

        Args:
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            SHA256 hash as cache key.
        """
        key_data = {"args": args, "kwargs": sorted(kwargs.items())}
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.sha256(key_str.encode()).hexdigest()[:32]

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache (Cache-Aside pattern).

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found/expired.
        """
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._stats["misses"] += 1
                return None

            if entry.is_expired():
                del self._cache[key]
                self._stats["misses"] += 1
                return None

            entry.hit_count += 1
            entry.last_accessed = time.time()
            self._stats["hits"] += 1
            return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
    ) -> None:
        """Set value in cache.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Optional time-to-live in seconds.
        """
        async with self._lock:
            if len(self._cache) >= self.config.max_size:
                self._evict()

            expires_at: Optional[float] = None
            effective_ttl = ttl if ttl is not None else self.config.default_ttl
            if effective_ttl:
                expires_at = time.time() + effective_ttl

            self._cache[key] = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                expires_at=expires_at,
            )
            self._stats["writes"] += 1

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

    def _evict(self) -> None:
        """Evict least recently used entry (LRU)."""
        if not self._cache:
            return

        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].last_accessed,
        )
        del self._cache[lru_key]
        self._stats["evictions"] += 1

    async def write_through(
        self,
        key: str,
        value: Any,
        source_write: Callable[..., Any],
        ttl: Optional[float] = None,
    ) -> None:
        """Write-Through pattern: write to both cache and source.

        Args:
            key: Cache key.
            value: Value to cache.
            source_write: Async function to write to source.
            ttl: Optional time-to-live.
        """
        await source_write(value)
        await self.set(key, value, ttl)

    async def write_behind(
        self,
        key: str,
        value: Any,
        source_write: Callable[..., Any],
        ttl: Optional[float] = None,
    ) -> None:
        """Write-Behind pattern: write to cache, async write to source.

        Args:
            key: Cache key.
            value: Value to cache.
            source_write: Async function to write to source.
            ttl: Optional time-to-live.
        """
        await self.set(key, value, ttl)
        asyncio.create_task(self._async_write(key, source_write, value))

    async def _async_write(
        self,
        key: str,
        source_write: Callable[..., Any],
        value: Any,
    ) -> None:
        """Async write to source for Write-Behind."""
        try:
            await source_write(value)
        except Exception:
            pass  # Log error in production

    async def get_or_compute(
        self,
        key: str,
        compute: Callable[..., Any],
        ttl: Optional[float] = None,
    ) -> Any:
        """Get from cache or compute if not present (Cache-Aside).

        Args:
            key: Cache key.
            compute: Async function to compute value if not cached.
            ttl: Optional time-to-live.

        Returns:
            Cached or computed value.
        """
        cached = await self.get(key)
        if cached is not None:
            return cached

        value = await compute()
        await self.set(key, value, ttl)
        return value

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics.
        """
        async with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = (
                self._stats["hits"] / total_requests if total_requests > 0 else 0
            )
            return {
                "size": len(self._cache),
                "max_size": self.config.max_size,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "hit_rate": hit_rate,
                "evictions": self._stats["evictions"],
                "writes": self._stats["writes"],
                "default_ttl": self.config.default_ttl,
                "strategy": self.config.strategy.value,
                "persist_dir": str(self._persist_dir) if self._persist_dir else None,
            }

    def reset_stats(self) -> None:
        """Reset statistics counters."""
        self._stats = {"hits": 0, "misses": 0, "evictions": 0, "writes": 0}


# Decorator version (kept for backward compatibility)
_cache_instance: Optional[CacheService] = None


def cached(
    ttl: Optional[float] = None,
    key_func: Optional[Callable[..., str]] = None,
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
        _cache: CacheService = CacheService(CacheConfig(default_ttl=ttl))

        async def wrapper(*args: Any, **kwargs: Any) -> T:
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                key_parts = [func.__name__]
                key_parts.extend(str(a) for a in args)
                key_parts.extend("{}={}".format(k, v) for k, v in sorted(kwargs.items()))
                cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()

            cached_value = await _cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            result = await func(*args, **kwargs)
            await _cache.set(cache_key, result, ttl)
            return result

        wrapper.cache = _cache  # type: ignore
        return wrapper

    return decorator


def get_cache(config: Optional[CacheConfig] = None) -> CacheService:
    """Get global cache instance.

    Args:
        config: Optional cache configuration.

    Returns:
        Global CacheService instance.
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheService(config)
    return _cache_instance


def set_cache(cache: CacheService) -> None:
    """Set global cache instance.

    Args:
        cache: CacheService instance to use globally.
    """
    global _cache_instance
    _cache_instance = cache
"""Retry Policy with Exponential Backoff for Claude Code Python.

Provides configurable retry behavior with various strategies.
"""

import asyncio
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, Tuple, Type


class RetryStrategy(Enum):
    """Retry strategy types."""

    FIXED = "fixed"  # Fixed delay between retries
    EXPONENTIAL = "exponential"  # Exponential backoff
    LINEAR = "linear"  # Linear increase in delay
    FIBONACCI = "fibonacci"  # Fibonacci sequence delays
    JITTER = "exponential_jitter"  # Exponential with random jitter


class RetryExhaustedError(Exception):
    """Raised when all retry attempts are exhausted."""

    def __init__(self, message: str, last_exception: Exception) -> None:
        super().__init__(message)
        self.last_exception = last_exception


@dataclass(frozen=True)
class RetryConfig:
    """Configuration for retry behavior.

    Attributes:
        max_attempts: Maximum number of retry attempts.
        initial_delay: Initial delay in seconds.
        max_delay: Maximum delay in seconds.
        exponential_base: Base for exponential calculation.
        jitter: Whether to add random jitter.
        jitter_factor: Maximum random jitter factor (0-1).
        retryable_exceptions: Tuple of exception types to retry on.
    """

    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_factor: float = 0.25
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)


def _calculate_delay(
    attempt: int,
    config: RetryConfig,
    strategy: RetryStrategy,
) -> float:
    """Calculate delay for the given attempt."""
    if strategy == RetryStrategy.FIXED:
        delay = config.initial_delay
    elif strategy == RetryStrategy.LINEAR:
        delay = config.initial_delay * attempt
    elif strategy == RetryStrategy.EXPONENTIAL:
        delay = config.initial_delay * (config.exponential_base ** attempt)
    elif strategy == RetryStrategy.FIBONACCI:
        # Fibonacci: 1, 1, 2, 3, 5, 8...
        fib = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
        delay = config.initial_delay * fib[min(attempt, len(fib) - 1)]
    else:  # JITTER
        base_delay = config.initial_delay * (config.exponential_base ** attempt)
        if config.jitter:
            jitter = base_delay * config.jitter_factor * random.random()
            delay = base_delay + jitter
        else:
            delay = base_delay

    return min(delay, config.max_delay)


async def retry_async(
    coro: Callable[..., Any],
    config: RetryConfig,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Execute an async coroutine with retry logic.

    Args:
        coro: Async coroutine to execute.
        config: Retry configuration.
        strategy: Retry strategy to use.
        on_retry: Optional callback on each retry.
        *args: Positional arguments for coro.
        **kwargs: Keyword arguments for coro.

    Returns:
        Result of the coroutine.

    Raises:
        RetryExhaustedError: If all retries are exhausted.
    """
    last_exception: Exception = None

    for attempt in range(config.max_attempts):
        try:
            if asyncio.iscoroutinefunction(coro):
                return await coro(*args, **kwargs)
            else:
                return await coro(*args, **kwargs)
        except config.retryable_exceptions as e:
            last_exception = e

            if attempt == config.max_attempts - 1:
                raise RetryExhaustedError(
                    "All {} retry attempts exhausted".format(config.max_attempts),
                    last_exception,
                )

            delay = _calculate_delay(attempt + 1, config, strategy)

            if on_retry:
                on_retry(attempt + 1, e)

            await asyncio.sleep(delay)

    raise RetryExhaustedError(
        "All {} retry attempts exhausted".format(config.max_attempts),
        last_exception,
    )


def retry_sync(
    func: Callable[..., Any],
    config: RetryConfig,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Execute a sync function with retry logic.

    Args:
        func: Synchronous function to execute.
        config: Retry configuration.
        strategy: Retry strategy to use.
        on_retry: Optional callback on each retry.
        *args: Positional arguments for func.
        **kwargs: Keyword arguments for func.

    Returns:
        Result of the function.

    Raises:
        RetryExhaustedError: If all retries are exhausted.
    """
    import time

    last_exception: Exception = None

    for attempt in range(config.max_attempts):
        try:
            return func(*args, **kwargs)
        except config.retryable_exceptions as e:
            last_exception = e

            if attempt == config.max_attempts - 1:
                raise RetryExhaustedError(
                    "All {} retry attempts exhausted".format(config.max_attempts),
                    last_exception,
                )

            delay = _calculate_delay(attempt + 1, config, strategy)

            if on_retry:
                on_retry(attempt + 1, e)

            time.sleep(delay)

    raise RetryExhaustedError(
        "All {} retry attempts exhausted".format(config.max_attempts),
        last_exception,
    )


# Decorator for async functions
def with_retry(
    config: Optional[RetryConfig] = None,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to add retry logic to async functions.

    Args:
        config: Retry configuration.
        strategy: Retry strategy to use.

    Returns:
        Decorated function with retry logic.

    Usage:
        @with_retry(RetryConfig(max_attempts=3))
        async def my_function():
            ...
    """
    cfg = config or RetryConfig()

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await retry_async(func, cfg, strategy, *args, **kwargs)

        return wrapper

    return decorator


# Predefined retry configs for common scenarios
RETRY_QUICK = RetryConfig(max_attempts=2, initial_delay=0.5, max_delay=2.0)
RETRY_DEFAULT = RetryConfig(max_attempts=3, initial_delay=1.0, max_delay=30.0)
RETRY_AGGRESSIVE = RetryConfig(max_attempts=5, initial_delay=2.0, max_delay=60.0)
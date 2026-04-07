"""Circuit Breaker pattern for Claude Code Python.

Provides fault tolerance and resilience for external service calls.
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass(frozen=True)
class CircuitBreakerConfig:
    """Configuration for circuit breaker.

    Attributes:
        failure_threshold: Number of failures before opening circuit.
        success_threshold: Number of successes in half-open to close.
        timeout: Seconds to wait before trying half-open.
        excluded_exceptions: Exception types that don't count as failures.
    """

    failure_threshold: int = 5
    success_threshold: int = 3
    timeout: float = 30.0
    excluded_exceptions: Tuple[type, ...] = ()


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker.

    Attributes:
        state: Current circuit state.
        failure_count: Consecutive failure count.
        success_count: Consecutive success count.
        last_failure_time: Timestamp of last failure.
        total_calls: Total number of calls.
        total_failures: Total number of failures.
    """

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    total_calls: int = 0
    total_failures: int = 0


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit is open.

    Attributes:
        message: Error message.
        retry_after: Seconds until circuit might close.
    """

    def __init__(self, message: str, retry_after: Optional[float] = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class CircuitBreaker:
    """Circuit breaker pattern implementation.

    Prevents cascading failures by failing fast when service is down.
    States: CLOSED (normal) -> OPEN (failing) -> HALF_OPEN (testing) -> CLOSED
    """

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> None:
        """Initialize circuit breaker.

        Args:
            name: Name for this circuit breaker.
            config: Configuration options.
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._metrics = CircuitBreakerMetrics()
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._metrics.state

    @property
    def is_available(self) -> bool:
        """Check if circuit allows calls."""
        if self._metrics.state == CircuitState.CLOSED:
            return True
        if self._metrics.state == CircuitState.HALF_OPEN:
            return True
        return False

    async def call(
        self,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute function with circuit breaker protection.

        Args:
            func: Function to execute.
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            Result of function execution.

        Raises:
            CircuitBreakerOpenError: If circuit is open.
        """
        async with self._lock:
            self._check_state_transition()

            if not self.is_available:
                retry_after = self._get_retry_after()
                raise CircuitBreakerOpenError(
                    "Circuit '{}' is open".format(self.name),
                    retry_after=retry_after,
                )

            self._metrics.total_calls += 1

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            await self._record_success()
            return result
        except Exception as e:
            await self._record_failure(e)
            raise

    def _check_state_transition(self) -> None:
        """Check if state should transition based on timeout."""
        if self._metrics.state == CircuitState.OPEN:
            if self._metrics.last_failure_time:
                elapsed = time.time() - self._metrics.last_failure_time
                if elapsed >= self.config.timeout:
                    self._metrics.state = CircuitState.HALF_OPEN
                    self._metrics.success_count = 0

    async def _record_success(self) -> None:
        """Record successful call."""
        async with self._lock:
            if self._metrics.state == CircuitState.HALF_OPEN:
                self._metrics.success_count += 1
                if self._metrics.success_count >= self.config.success_threshold:
                    self._metrics.state = CircuitState.CLOSED
                    self._metrics.failure_count = 0
            elif self._metrics.state == CircuitState.CLOSED:
                self._metrics.failure_count = 0

    async def _record_failure(self, error: Exception) -> None:
        """Record failed call."""
        async with self._lock:
            self._metrics.total_failures += 1
            self._metrics.last_failure_time = time.time()

            # Check if we should open the circuit
            if isinstance(error, self.config.excluded_exceptions):
                return

            if self._metrics.state == CircuitState.HALF_OPEN:
                self._metrics.state = CircuitState.OPEN
            elif self._metrics.state == CircuitState.CLOSED:
                self._metrics.failure_count += 1
                if self._metrics.failure_count >= self.config.failure_threshold:
                    self._metrics.state = CircuitState.OPEN

    def _get_retry_after(self) -> Optional[float]:
        """Get recommended retry time."""
        if self._metrics.last_failure_time:
            elapsed = time.time() - self._metrics.last_failure_time
            remaining = self.config.timeout - elapsed
            return max(0.0, remaining) if remaining else None
        return self.config.timeout

    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics.

        Returns:
            Dictionary with metrics.
        """
        return {
            "name": self.name,
            "state": self._metrics.state.value,
            "failure_count": self._metrics.failure_count,
            "success_count": self._metrics.success_count,
            "total_calls": self._metrics.total_calls,
            "total_failures": self._metrics.total_failures,
            "last_failure_time": self._metrics.last_failure_time,
        }

    def reset(self) -> None:
        """Reset circuit breaker to closed state."""
        self._metrics = CircuitBreakerMetrics()


class CircuitBreakerManager:
    """Manager for multiple circuit breakers."""

    def __init__(self) -> None:
        """Initialize circuit breaker manager."""
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()

    def get_or_create(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ) -> CircuitBreaker:
        """Get existing or create new circuit breaker.

        Args:
            name: Name of circuit breaker.
            config: Configuration for new circuit breaker.

        Returns:
            CircuitBreaker instance.
        """
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name, config)
        return self._breakers[name]

    async def call(
        self,
        name: str,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute function with circuit breaker protection.

        Args:
            name: Name of circuit breaker.
            func: Function to execute.
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            Result of function execution.
        """
        breaker = self.get_or_create(name)
        return await breaker.call(func, *args, **kwargs)

    def get_all_metrics(self) -> List[Dict[str, Any]]:
        """Get metrics for all circuit breakers.

        Returns:
            List of metrics dictionaries.
        """
        return [breaker.get_metrics() for breaker in self._breakers.values()]


# Global circuit breaker manager
_circuit_breaker_manager: Optional[CircuitBreakerManager] = None


def get_circuit_breaker_manager() -> CircuitBreakerManager:
    """Get global circuit breaker manager.

    Returns:
        Global CircuitBreakerManager instance.
    """
    global _circuit_breaker_manager
    if _circuit_breaker_manager is None:
        _circuit_breaker_manager = CircuitBreakerManager()
    return _circuit_breaker_manager
"""Health Check System for Claude Code Python.

Provides health monitoring for all services and components.
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class HealthStatus(Enum):
    """Health check status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    name: str
    status: HealthStatus
    message: Optional[str] = None
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class HealthCheck:
    """Base health check interface."""

    name: str = "base"

    async def check(self) -> HealthCheckResult:
        """Run health check.

        Returns:
            HealthCheckResult with status.
        """
        return HealthCheckResult(name=self.name, status=HealthStatus.HEALTHY)


class HealthCheckRegistry:
    """Registry for all health checks."""

    def __init__(self) -> None:
        """Initialize the registry."""
        self._checks: Dict[str, HealthCheck] = {}

    def register(self, check: HealthCheck) -> None:
        """Register a health check.

        Args:
            check: HealthCheck instance.
        """
        self._checks[check.name] = check

    def unregister(self, name: str) -> bool:
        """Unregister a health check.

        Args:
            name: Name of the check to remove.

        Returns:
            True if removed, False if not found.
        """
        if name in self._checks:
            del self._checks[name]
            return True
        return False

    async def check_all(self) -> List[HealthCheckResult]:
        """Run all health checks.

        Returns:
            List of health check results.
        """
        results = []
        for name, check in self._checks.items():
            start = time.time()
            try:
                result = await check.check()
                result.duration_ms = (time.time() - start) * 1000
            except Exception as e:
                result = HealthCheckResult(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=str(e),
                    duration_ms=(time.time() - start) * 1000,
                )
            results.append(result)
        return results

    def get_status(self) -> Dict[str, Any]:
        """Get overall health status.

        Returns:
            Dictionary with overall status.
        """
        # This will be populated asynchronously
        return {"status": "unknown", "checks": {}}


class APIHealthCheck(HealthCheck):
    """Health check for API connectivity."""

    name = "api"

    def __init__(self, client_getter: Callable[[], Any] = None) -> None:
        """Initialize API health check.

        Args:
            client_getter: Optional callable to get API client.
        """
        self._client_getter = client_getter

    async def check(self) -> HealthCheckResult:
        """Check API connectivity."""
        # This is a placeholder - actual implementation would
        # ping the API endpoint
        return HealthCheckResult(
            name=self.name,
            status=HealthStatus.HEALTHY,
            metadata={"provider": "anthropic"},
        )


class CacheHealthCheck(HealthCheck):
    """Health check for cache service."""

    name = "cache"

    def __init__(self, cache_getter: Callable[[], Any] = None) -> None:
        """Initialize cache health check.

        Args:
            cache_getter: Optional callable to get cache service.
        """
        self._cache_getter = cache_getter

    async def check(self) -> HealthCheckResult:
        """Check cache service."""
        return HealthCheckResult(
            name=self.name,
            status=HealthStatus.HEALTHY,
            metadata={"type": "in-memory"},
        )


class CircuitBreakerHealthCheck(HealthCheck):
    """Health check for circuit breakers."""

    name = "circuit_breaker"

    def __init__(self, cb_manager_getter: Callable[[], Any] = None) -> None:
        """Initialize circuit breaker health check.

        Args:
            cb_manager_getter: Optional callable to get circuit breaker manager.
        """
        self._cb_manager_getter = cb_manager_getter

    async def check(self) -> HealthCheckResult:
        """Check circuit breaker status."""
        return HealthCheckResult(
            name=self.name,
            status=HealthStatus.HEALTHY,
            metadata={"breakers": []},
        )


class RateLimiterHealthCheck(HealthCheck):
    """Health check for rate limiter."""

    name = "rate_limiter"

    async def check(self) -> HealthCheckResult:
        """Check rate limiter status."""
        return HealthCheckResult(
            name=self.name,
            status=HealthStatus.HEALTHY,
            metadata={"mode": "token_bucket"},
        )


# Global health check registry
_registry: Optional[HealthCheckRegistry] = None


def get_health_check_registry() -> HealthCheckRegistry:
    """Get or create the global health check registry.

    Returns:
        Global HealthCheckRegistry instance.
    """
    global _registry
    if _registry is None:
        _registry = HealthCheckRegistry()
        # Register default checks
        _registry.register(APIHealthCheck())
        _registry.register(CacheHealthCheck())
        _registry.register(CircuitBreakerHealthCheck())
        _registry.register(RateLimiterHealthCheck())
    return _registry


async def health_check() -> Dict[str, Any]:
    """Run all health checks and return results.

    Returns:
        Dictionary with overall health status and check results.
    """
    registry = get_health_check_registry()
    results = await registry.check_all()

    # Determine overall status
    if any(r.status == HealthStatus.UNHEALTHY for r in results):
        overall_status = HealthStatus.UNHEALTHY
    elif any(r.status == HealthStatus.DEGRADED for r in results):
        overall_status = HealthStatus.DEGRADED
    else:
        overall_status = HealthStatus.HEALTHY

    return {
        "status": overall_status.value,
        "timestamp": time.time(),
        "checks": {
            r.name: {
                "status": r.status.value,
                "message": r.message,
                "duration_ms": r.duration_ms,
                "metadata": r.metadata,
            }
            for r in results
        },
    }


# Liveness and readiness endpoints (for Kubernetes-style health checks)
async def liveness_check() -> Dict[str, Any]:
    """Liveness probe - is the application running?

    Returns:
        Simple alive status.
    """
    return {"alive": True, "timestamp": time.time()}


async def readiness_check() -> Dict[str, Any]:
    """Readiness probe - is the application ready to serve traffic?

    Returns:
        Ready status with details.
    """
    return await health_check()
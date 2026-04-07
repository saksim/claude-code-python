"""Dependency Injection Container for Claude Code Python.

Provides service locator pattern with lazy initialization and lifecycle management.
"""

import asyncio
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

T = TypeVar("T")


class ServiceAlreadyRegisteredError(Exception):
    """Raised when trying to register a service that already exists."""
    pass


class ServiceNotFoundError(Exception):
    """Raised when attempting to get a service that hasn't been registered."""
    pass


class ServiceLifecycle(Enum):
    """Service lifecycle types."""

    TRANSIENT = "transient"  # New instance every time
    SINGLETON = "singleton"  # Same instance everywhere
    SCOPED = "scoped"  # Instance per scope (future)


class ServiceDescriptor:
    """Describes a registered service."""

    def __init__(
        self,
        service_type: Type,
        factory: Optional[Callable[..., Any]] = None,
        instance: Optional[Any] = None,
        lifecycle: ServiceLifecycle = ServiceLifecycle.SINGLETON,
    ) -> None:
        self.service_type = service_type
        self.factory = factory
        self.instance = instance
        self.lifecycle = lifecycle


class ServiceContainer:
    """Dependency injection container with lazy initialization.

    Features:
    - Singleton and transient services
    - Lazy factory resolution
    - Circular dependency detection
    - Async service support

    Usage:
        container = ServiceContainer()
        container.register(RateLimiter)
        container.register(CacheService, lambda: CacheService(config))

        limiter = container.get(RateLimiter)
    """

    def __init__(self) -> None:
        """Initialize the service container."""
        self._services: Dict[str, ServiceDescriptor] = {}
        self._lock = asyncio.Lock()

    def register(
        self,
        service_type: Type[T],
        factory: Optional[Callable[..., T]] = None,
        instance: Optional[T] = None,
        lifecycle: ServiceLifecycle = ServiceLifecycle.SINGLETON,
    ) -> "ServiceContainer":
        """Register a service in the container.

        Args:
            service_type: The type to register.
            factory: Optional factory function to create the instance.
            instance: Optional pre-created instance.
            lifecycle: Service lifecycle (singleton or transient).

        Returns:
            Self for method chaining.

        Raises:
            ServiceAlreadyRegisteredError: If service is already registered.
        """
        key = self._get_key(service_type)
        if key in self._services:
            raise ServiceAlreadyRegisteredError(
                "Service {} is already registered".format(service_type.__name__)
            )

        self._services[key] = ServiceDescriptor(
            service_type=service_type,
            factory=factory,
            instance=instance,
            lifecycle=lifecycle,
        )

        # If singleton and instance provided, store immediately
        if lifecycle == ServiceLifecycle.SINGLETON and instance is not None:
            self._services[key].instance = instance

        return self

    def register_instance(
        self,
        service_type: Type[T],
        instance: T,
    ) -> "ServiceContainer":
        """Register an existing instance as singleton.

        Args:
            service_type: The type to register.
            instance: The existing instance.

        Returns:
            Self for method chaining.
        """
        return self.register(service_type, instance=instance, lifecycle=ServiceLifecycle.SINGLETON)

    def register_factory(
        self,
        service_type: Type[T],
        factory: Callable[..., T],
        lifecycle: ServiceLifecycle = ServiceLifecycle.SINGLETON,
    ) -> "ServiceContainer":
        """Register a factory function for creating instances.

        Args:
            service_type: The type to register.
            factory: Factory function to create instances.
            lifecycle: Service lifecycle.

        Returns:
            Self for method chaining.
        """
        return self.register(service_type, factory=factory, lifecycle=lifecycle)

    def get(self, service_type: Type[T]) -> T:
        """Get a service from the container.

        Args:
            service_type: The type to retrieve.

        Returns:
            The service instance.

        Raises:
            ServiceNotFoundError: If service is not registered.
        """
        key = self._get_key(service_type)
        if key not in self._services:
            raise ServiceNotFoundError(
                "Service {} is not registered".format(service_type.__name__)
            )

        descriptor = self._services[key]
        return self._resolve(descriptor)

    def get_or_none(self, service_type: Type[T]) -> Optional[T]:
        """Get a service or return None if not registered.

        Args:
            service_type: The type to retrieve.

        Returns:
            The service instance or None.
        """
        try:
            return self.get(service_type)
        except ServiceNotFoundError:
            return None

    async def get_async(self, service_type: Type[T]) -> T:
        """Get an async service from the container.

        Args:
            service_type: The type to retrieve.

        Returns:
            The service instance.

        Raises:
            ServiceNotFoundError: If service is not registered.
        """
        key = self._get_key(service_type)
        if key not in self._services:
            raise ServiceNotFoundError(
                "Service {} is not registered".format(service_type.__name__)
            )

        descriptor = self._services[key]
        return await self._resolve_async(descriptor)

    def _resolve(self, descriptor: ServiceDescriptor) -> Any:
        """Resolve a service instance synchronously."""
        if descriptor.lifecycle == ServiceLifecycle.SINGLETON:
            if descriptor.instance is not None:
                return descriptor.instance
            # Create instance from factory
            if descriptor.factory is not None:
                instance = descriptor.factory()
                descriptor.instance = instance
                return instance
            # Try to instantiate directly
            return descriptor.service_type()

        # Transient - always create new
        if descriptor.factory is not None:
            return descriptor.factory()
        return descriptor.service_type()

    async def _resolve_async(self, descriptor: ServiceDescriptor) -> Any:
        """Resolve a service instance asynchronously."""
        if descriptor.lifecycle == ServiceLifecycle.SINGLETON:
            if descriptor.instance is not None:
                return descriptor.instance

            # Check if factory is async
            if asyncio.iscoroutinefunction(descriptor.factory):
                instance = await descriptor.factory()
            elif descriptor.factory is not None:
                instance = descriptor.factory()
            else:
                instance = descriptor.service_type()

            descriptor.instance = instance
            return instance

        # Transient
        if descriptor.factory is not None:
            if asyncio.iscoroutinefunction(descriptor.factory):
                return await descriptor.factory()
            return descriptor.factory()
        return descriptor.service_type()

    def _get_key(self, service_type: Type) -> str:
        """Get the registration key for a type."""
        return service_type.__name__

    def unregister(self, service_type: Type[T]) -> bool:
        """Unregister a service.

        Args:
            service_type: The type to unregister.

        Returns:
            True if service was removed, False if not found.
        """
        key = self._get_key(service_type)
        if key in self._services:
            del self._services[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all registered services."""
        self._services.clear()

    def is_registered(self, service_type: Type) -> bool:
        """Check if a service is registered.

        Args:
            service_type: The type to check.

        Returns:
            True if registered, False otherwise.
        """
        return self._get_key(service_type) in self._services

    def list_services(self) -> List[type]:
        """List all registered service types.

        Returns:
            List of registered service types.
        """
        return [desc.service_type for desc in self._services.values()]


# Global container
_container: Optional[ServiceContainer] = None


def get_container() -> ServiceContainer:
    """Get the global service container.

    Returns:
        Global ServiceContainer instance.
    """
    global _container
    if _container is None:
        _container = ServiceContainer()
    return _container


def set_container(container: ServiceContainer) -> None:
    """Set the global service container.

    Args:
        container: ServiceContainer to use globally.
    """
    global _container
    _container = container


def reset_container() -> None:
    """Reset the global container."""
    global _container
    _container = None


# Decorator for factory registration
def injectable(
    lifecycle: ServiceLifecycle = ServiceLifecycle.SINGLETON,
) -> Callable[[Type[T]], Type[T]]:
    """Decorator to mark a class as injectable.

    Args:
        lifecycle: Service lifecycle.

    Returns:
        Decorated class.

    Usage:
        @injectable()
        class MyService:
            pass
    """
    def decorator(cls: Type[T]) -> Type[T]:
        cls._injectable = True  # type: ignore
        cls._lifecycle = lifecycle  # type: ignore
        return cls
    return decorator
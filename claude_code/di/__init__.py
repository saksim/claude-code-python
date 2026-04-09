"""
Claude Code Python - Dependency Injection Module

Provides service container and dependency injection patterns.
"""

from claude_code.di.container import (
    ServiceContainer,
    ServiceLifecycle,
    ServiceDescriptor,
    ServiceAlreadyRegisteredError,
    ServiceNotFoundError,
    CircularDependencyError,
    get_container,
    set_container,
    reset_container,
    injectable,
)

__all__ = [
    "ServiceContainer",
    "ServiceLifecycle",
    "ServiceDescriptor",
    "ServiceAlreadyRegisteredError",
    "ServiceNotFoundError",
    "CircularDependencyError",
    "get_container",
    "set_container",
    "reset_container",
    "injectable",
]
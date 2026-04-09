"""Unified State Manager for Claude Code Python.

Provides a single entry point for all global state in the application.
This simplifies state access and improves testability.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Protocol-based design for extensibility
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from claude_code.di.container import ServiceContainer
    from claude_code.config import Config
    from claude_code.services.telemetry_service import TelemetryService
    from claude_code.services.cache_service import CacheService
    from claude_code.services.event_bus import EventBus

logger = logging.getLogger(__name__)


class StateManager:
    """Unified state manager providing access to all global state.
    
    This class serves as a central registry for accessing global services
    and state within the Claude Code application. It provides a unified
    interface that simplifies state access and improves testability.
    
    Attributes:
        _container: The dependency injection container
        _config: Global configuration instance
        _telemetry: Global telemetry service
        _cache: Global cache service
        _event_bus: Global event bus
        _initialized: Whether the state manager has been initialized
    
    Example:
        >>> from claude_code.state.manager import StateManager
        >>> 
        >>> # Get configuration
        >>> config = StateManager.get_config()
        >>> 
        >>> # Get service from container
        >>> rate_limiter = StateManager.get_container().get(RateLimiter)
        >>> 
        >>> # Check initialization
        >>> if StateManager.is_initialized():
        ...     print("StateManager ready")
    """
    
    _container: Optional[ServiceContainer] = None
    _config: Optional[Config] = None
    _telemetry: Optional[TelemetryService] = None
    _cache: Optional[CacheService] = None
    _event_bus: Optional[EventBus] = None
    _initialized: bool = False
    
    @classmethod
    def initialize(
        cls,
        container: ServiceContainer,
        config: Config,
        telemetry: Optional[TelemetryService] = None,
        cache: Optional[CacheService] = None,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        """Initialize the state manager with global services.
        
        Args:
            container: The dependency injection container
            config: Global configuration instance
            telemetry: Optional telemetry service
            cache: Optional cache service
            event_bus: Optional event bus
        """
        cls._container = container
        cls._config = config
        cls._telemetry = telemetry
        cls._cache = cache
        cls._event_bus = event_bus
        cls._initialized = True
        logger.info("StateManager initialized")
    
    @classmethod
    def reset(cls) -> None:
        """Reset all state - useful for testing."""
        cls._container = None
        cls._config = None
        cls._telemetry = None
        cls._cache = None
        cls._event_bus = None
        cls._initialized = False
        logger.debug("StateManager reset")
    
    @classmethod
    def is_initialized(cls) -> bool:
        """Check if the state manager is initialized.
        
        Returns:
            True if initialized, False otherwise
        """
        return cls._initialized
    
    @classmethod
    def get_container(cls) -> ServiceContainer:
        """Get the dependency injection container.
        
        Returns:
            The service container
            
        Raises:
            RuntimeError: If state manager not initialized
        """
        if not cls._initialized:
            raise RuntimeError("StateManager not initialized. Call initialize() first.")
        if cls._container is None:
            raise RuntimeError("Container not set")
        return cls._container
    
    @classmethod
    def get_config(cls) -> Config:
        """Get the global configuration.
        
        Returns:
            The configuration instance
            
        Raises:
            RuntimeError: If state manager not initialized
        """
        if not cls._initialized:
            raise RuntimeError("StateManager not initialized. Call initialize() first.")
        if cls._config is None:
            raise RuntimeError("Config not set")
        return cls._config
    
    @classmethod
    def get_telemetry(cls) -> Optional[TelemetryService]:
        """Get the telemetry service.
        
        Returns:
            The telemetry service or None if not available
        """
        return cls._telemetry
    
    @classmethod
    def get_cache(cls) -> Optional[CacheService]:
        """Get the cache service.
        
        Returns:
            The cache service or None if not available
        """
        return cls._cache
    
    @classmethod
    def get_event_bus(cls) -> Optional[EventBus]:
        """Get the event bus.
        
        Returns:
            The event bus or None if not available
        """
        return cls._event_bus
    
    @classmethod
    def get_service(cls, service_type: type) -> Any:
        """Get a service from the container.
        
        Args:
            service_type: The type of service to retrieve
            
        Returns:
            The service instance
            
        Raises:
            RuntimeError: If state manager not initialized
        """
        return cls.get_container().get(service_type)
    
    @classmethod
    def get_service_or_none(cls, service_type: type) -> Optional[Any]:
        """Get a service or None if not registered.
        
        Args:
            service_type: The type of service to retrieve
            
        Returns:
            The service instance or None
        """
        container = cls._container
        if container is None:
            return None
        return container.get_or_none(service_type)
    
    @classmethod
    def get_state_summary(cls) -> dict[str, Any]:
        """Get a summary of the current state.
        
        Returns:
            Dictionary containing state information
        """
        return {
            "initialized": cls._initialized,
            "has_container": cls._container is not None,
            "has_config": cls._config is not None,
            "has_telemetry": cls._telemetry is not None,
            "has_cache": cls._cache is not None,
            "has_event_bus": cls._event_bus is not None,
        }


__all__ = ["StateManager"]
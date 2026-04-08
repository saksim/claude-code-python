"""Claude Code Python - Complete Application Framework.

Provides unified application lifecycle management integrating all components.
"""

import asyncio
import signal
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Optional

# Import DI container directly to avoid circular imports
import importlib.util
spec = importlib.util.spec_from_file_location("di_container", "claude_code/di/container.py")
di_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(di_module)
ServiceContainer = di_module.ServiceContainer
ServiceLifecycle = di_module.ServiceLifecycle
get_container = di_module.get_container
set_container = di_module.set_container

# Import services
spec2 = importlib.util.spec_from_file_location("services", "claude_code/services/__init__.py")
# Skip this, import individually

# Import shutdown
spec3 = importlib.util.spec_from_file_location("shutdown", "claude_code/services/shutdown.py")
shutdown_module = importlib.util.module_from_spec(spec3)
spec3.loader.exec_module(shutdown_module)
ShutdownManager = shutdown_module.ShutdownManager
ShutdownConfig = shutdown_module.ShutdownConfig

# Import config manager
spec4 = importlib.util.spec_from_file_location("config_manager", "claude_code/utils/config_manager.py")
config_module = importlib.util.module_from_spec(spec4)
spec4.loader.exec_module(config_module)
ConfigManager = config_module.ConfigManager
get_config_manager = config_module.get_config_manager

# Import tracing
spec5 = importlib.util.spec_from_file_location("tracing", "claude_code/utils/tracing.py")
tracing_module = importlib.util.module_from_spec(spec5)
spec5.loader.exec_module(tracing_module)
Tracer = tracing_module.Tracer
get_tracer = tracing_module.get_tracer

# Import request context
spec6 = importlib.util.spec_from_file_location("request_context", "claude_code/utils/request_context.py")
rc_module = importlib.util.module_from_spec(spec6)
spec6.loader.exec_module(rc_module)
RequestContextManager = rc_module.RequestContextManager
generate_request_id = rc_module.generate_request_id
get_request_id = rc_module.get_request_id
get_correlation_id = rc_module.get_correlation_id

# Import logger
spec7 = importlib.util.spec_from_file_location("logging_system", "claude_code/utils/logging_system.py")
logger_module = importlib.util.module_from_spec(spec7)
spec7.loader.exec_module(logger_module)
get_logger = logger_module.get_logger
setup_logging = logger_module.configure_logging


class AppPhase(Enum):
    """Application lifecycle phases."""

    INITIALIZING = "initializing"
    RUNNING = "running"
    SHUTTING_DOWN = "shutting_down"
    STOPPED = "stopped"


@dataclass
class AppConfig:
    """Main application configuration.

    Attributes:
        service_name: Name of the service.
        version: Application version.
        config_dir: Directory for configuration files.
        log_level: Logging level.
        enable_telemetry: Enable telemetry.
        enable_tracing: Enable distributed tracing.
        enable_health_check: Enable health check endpoint.
    """

    service_name: str = "claude-code"
    version: str = "1.0.0"
    config_dir: Optional[Path] = None
    log_level: str = "INFO"
    enable_telemetry: bool = True
    enable_tracing: bool = True
    enable_health_check: bool = True


class Application:
    """Complete application framework for Claude Code Python.

    Integrates:
    - Dependency Injection Container
    - Configuration Management
    - Logging & Tracing
    - Health Checks
    - Graceful Shutdown
    - Service Lifecycle

    Usage:
        async with Application(config) as app:
            await app.setup()
            # Register services
            app.register_service(RateLimiter)
            app.register_service(CacheService)

            await app.run()
    """

    def __init__(self, config: Optional[AppConfig] = None) -> None:
        """Initialize the application.

        Args:
            config: Application configuration.
        """
        self.config = config or AppConfig()
        self._phase = AppPhase.INITIALIZING
        self._services: Dict[str, Any] = {}
        self._logger = get_logger(self.config.service_name)
        
        # Core components (lazy initialized)
        self._container: Optional[ServiceContainer] = None
        self._config_manager: Optional[ConfigManager] = None
        self._tracer: Optional[Tracer] = None
        self._shutdown_manager: Optional[ShutdownManager] = None
        
        # State
        self._running = False

    async def __aenter__(self) -> "Application":
        """Enter application context."""
        await self._setup()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit application context."""
        await self._teardown(exc_val)

    async def _setup(self) -> None:
        """Setup all application components."""
        self._logger.info("Initializing %s v%s", self.config.service_name, self.config.version)
        
        # 1. Setup logging
        setup_logging(self.config.log_level)
        
        # 2. Initialize DI Container
        self._container = ServiceContainer()
        set_container(self._container)
        
        # 3. Initialize Configuration Manager
        self._config_manager = ConfigManager(
            env_prefix=f"{self.config.service_name.upper()}_",
            config_file=self.config.config_dir / "config.json" if self.config.config_dir else None
        )
        
        # 4. Initialize Tracing
        if self.config.enable_tracing:
            self._tracer = get_tracer(self.config.service_name)
            self._logger.info("Tracing enabled")
        
        # 5. Initialize Shutdown Manager
        shutdown_config = ShutdownConfig(
            on_shutdown=self._on_shutdown,
            on_cleanup=self._on_cleanup,
        )
        self._shutdown_manager = ShutdownManager(shutdown_config)
        await self._shutdown_manager.start()
        
        # 6. Register signal handlers
        self._register_signal_handlers()
        
        self._phase = AppPhase.RUNNING
        self._running = True
        self._logger.info("Application initialized successfully")

    async def _teardown(self, error: Optional[Exception]) -> None:
        """Teardown all application components."""
        if self._phase == AppPhase.SHUTTING_DOWN:
            return
            
        self._phase = AppPhase.SHUTTING_DOWN
        reason = f"Error: {error}" if error else "Normal exit"
        self._logger.info("Shutting down: %s", reason)
        
        # Run cleanup callbacks
        for name, cleanup in self._services.items():
            try:
                if asyncio.iscoroutinefunction(cleanup):
                    await cleanup()
                else:
                    cleanup()
                self._logger.debug("Cleaned up: %s", name)
            except Exception as e:
                self._logger.error("Error during cleanup %s: %s", name, e)
        
        if self._shutdown_manager:
            await self._shutdown_manager.shutdown(reason)
        
        self._phase = AppPhase.STOPPED
        self._running = False
        self._logger.info("Application stopped")

    def _register_signal_handlers(self) -> None:
        """Register signal handlers for graceful shutdown."""
        if sys.platform != "win32":
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop = asyncio.get_event_loop()
                loop.add_signal_handler(
                    sig,
                    lambda s=sig: asyncio.create_task(self._handle_signal(s)),
                )

    async def _handle_signal(self, sig: signal.Signals) -> None:
        """Handle shutdown signal."""
        await self._teardown(Exception(f"Received {sig.name}"))

    async def _on_shutdown(self) -> None:
        """Callback during shutdown."""
        self._logger.info("Shutdown initiated")

    async def _on_cleanup(self) -> None:
        """Callback for final cleanup."""
        self._logger.info("Final cleanup completed")

    def register_service(
        self,
        name: str,
        service: Any,
        cleanup: Optional[Callable[[], Any]] = None,
    ) -> None:
        """Register a service with optional cleanup callback.

        Args:
            name: Service name.
            service: Service instance.
            cleanup: Optional cleanup callback.
        """
        self._services[name] = cleanup
        self._container.register_instance(type(service), service)
        self._logger.debug("Registered service: %s", name)

    def register_factory(
        self,
        name: str,
        factory: Callable[..., Any],
        cleanup: Optional[Callable[[], Any]] = None,
    ) -> None:
        """Register a service factory.

        Args:
            name: Service name.
            factory: Service factory function.
            cleanup: Optional cleanup callback.
        """
        self._services[name] = cleanup
        self._container.register_factory(
            type(next(iter([factory()]))),  # Get type from factory result
            factory,
            ServiceLifecycle.SINGLETON,
        )
        self._logger.debug("Registered factory: %s", name)

    async def run(self) -> None:
        """Run the application main loop."""
        self._logger.info("Application running")
        
        while self._running:
            await asyncio.sleep(1)

    def stop(self) -> None:
        """Stop the application."""
        self._running = False

    @property
    def phase(self) -> AppPhase:
        """Get current application phase."""
        return self._phase

    @property
    def is_running(self) -> bool:
        """Check if application is running."""
        return self._running and self._phase == AppPhase.RUNNING

    @property
    def container(self) -> ServiceContainer:
        """Get the DI container."""
        return self._container

    @property
    def config_manager(self) -> ConfigManager:
        """Get the config manager."""
        return self._config_manager

    @property
    def tracer(self) -> Optional[Tracer]:
        """Get the tracer."""
        return self._tracer

    @property
    def logger(self) -> Any:
        """Get the logger."""
        return self._logger


# Application context for request-level operations
class AppContext:
    """Request-level application context.

    Provides access to services and request tracking.
    """

    def __init__(self, app: Application) -> None:
        """Initialize app context.

        Args:
            app: Parent Application instance.
        """
        self._app = app
        self._request_manager: Optional[RequestContextManager] = None

    async def __aenter__(self) -> "AppContext":
        """Enter context."""
        self._request_manager = RequestContextManager()
        await self._request_manager.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context."""
        if self._request_manager:
            await self._request_manager.__aexit__(exc_type, exc_val, exc_tb)

    @property
    def request_id(self) -> str:
        """Get current request ID."""
        return get_request_id() or generate_request_id()

    @property
    def correlation_id(self) -> str:
        """Get current correlation ID."""
        return get_correlation_id() or generate_request_id()

    def get_service(self, service_type: type) -> Any:
        """Get a service from the container.

        Args:
            service_type: Service type to retrieve.

        Returns:
            Service instance.
        """
        return self._app.container.get(service_type)

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key.
            default: Default value.

        Returns:
            Configuration value.
        """
        return self._app.config_manager.get(key, default)


# Global application instance
_app: Optional[Application] = None


def get_app() -> Optional[Application]:
    """Get the global application instance.

    Returns:
        Global Application or None.
    """
    return _app


def set_app(app: Application) -> None:
    """Set the global application instance.

    Args:
        app: Application to set globally.
    """
    global _app
    _app = app


# Convenience function to run the application
async def run_app(
    config: Optional[AppConfig] = None,
    setup_callback: Optional[Callable[[Application], None]] = None,
    run_callback: Optional[Callable[[Application], None]] = None,
) -> None:
    """Run the application with setup and run callbacks.

    Args:
        config: Application configuration.
        setup_callback: Callback to setup services.
        run_callback: Callback to run main logic.
    """
    async with Application(config) as app:
        if setup_callback:
            if asyncio.iscoroutinefunction(setup_callback):
                await setup_callback(app)
            else:
                setup_callback(app)

        if run_callback:
            if asyncio.iscoroutinefunction(run_callback):
                await run_callback(app)
            else:
                run_callback(app)
        else:
            await app.run()


# Example usage
if __name__ == "__main__":
    async def main():
        config = AppConfig(
            service_name="claude-code",
            version="1.0.0",
            log_level="DEBUG",
        )

        async with Application(config) as app:
            # Register services
            app.register_service("rate_limiter", get_rate_limiter())
            app.register_service("cache", get_cache())

            # Run
            await app.run()

    asyncio.run(main())
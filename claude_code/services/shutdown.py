"""Graceful Shutdown Manager for Claude Code Python.

Provides clean shutdown with resource cleanup and signal handling.
"""

import asyncio
import signal
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class ShutdownPhase(Enum):
    """Shutdown phases."""

    INITIATED = "initiated"
    DRAINING = "draining"
    STOPPING = "stopping"
    COMPLETED = "completed"


@dataclass
class ShutdownConfig:
    """Configuration for graceful shutdown."""

    timeout: float = 30.0  # seconds
    force_after: float = 60.0  # force kill after this
    on_shutdown: Optional[Callable[[], Any]] = None
    on_cleanup: Optional[Callable[[], Any]] = None


class ShutdownManager:
    """Manages graceful shutdown of the application.

    Features:
    - Signal handling (SIGINT, SIGTERM)
    - Phase-based shutdown
    - Resource cleanup callbacks
    - Force shutdown timeout

    Usage:
        manager = ShutdownManager(config)
        await manager.start()

        # Register cleanup callbacks
        manager.register_cleanup("cache", cleanup_cache)
        manager.register_cleanup("connections", close_connections)

        # On shutdown signal, graceful shutdown will trigger
    """

    def __init__(self, config: Optional[ShutdownConfig] = None) -> None:
        """Initialize shutdown manager.

        Args:
            config: Shutdown configuration.
        """
        self.config = config or ShutdownConfig()
        self._phase = ShutdownPhase.INITIATED
        self._cleanups: Dict[str, Callable[[], Any]] = {}
        self._running_tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
        self._force_task: Optional[asyncio.Task] = None
        self._original_signal_handlers: Dict[signal.Signals, Any] = {}

    async def start(self) -> None:
        """Start the shutdown manager and register signal handlers."""
        if sys.platform != "win32":
            # Register signal handlers for Unix-like systems
            for sig in (signal.SIGINT, signal.SIGTERM):
                self._original_signal_handlers[sig] = signal.getsignal(sig)
                loop = asyncio.get_event_loop()
                loop.add_signal_handler(
                    sig,
                    lambda s=sig: asyncio.create_task(self._handle_signal(s)),
                )

    async def _handle_signal(self, sig: signal.Signals) -> None:
        """Handle shutdown signal."""
        await self.shutdown(reason=f"Received {sig.name}")

    def register_cleanup(self, name: str, callback: Callable[[], Any]) -> None:
        """Register a cleanup callback.

        Args:
            name: Name of the cleanup task.
            callback: Async or sync callback to execute.
        """
        self._cleanups[name] = callback

    def register_task(self, task: asyncio.Task) -> None:
        """Register a running task to wait for during shutdown.

        Args:
            task: Task to monitor.
        """
        self._running_tasks.append(task)

    async def shutdown(self, reason: str = "unknown") -> None:
        """Initiate graceful shutdown.

        Args:
            reason: Reason for shutdown.
        """
        if self._phase == ShutdownPhase.COMPLETED:
            return

        print(f"Shutting down gracefully: {reason}")
        self._phase = ShutdownPhase.DRAINING

        # Call shutdown callback
        if self.config.on_shutdown:
            if asyncio.iscoroutinefunction(self.config.on_shutdown):
                await self.config.on_shutdown()
            else:
                self.config.on_shutdown()

        # Wait for running tasks with timeout
        if self._running_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._running_tasks, return_exceptions=True),
                    timeout=self.config.timeout,
                )
            except asyncio.TimeoutError:
                print("Warning: Some tasks did not complete in time")

        self._phase = ShutdownPhase.STOPPING

        # Run cleanup callbacks
        for name, cleanup in self._cleanups.items():
            try:
                if asyncio.iscoroutinefunction(cleanup):
                    await cleanup()
                else:
                    cleanup()
                print(f"Cleaned up: {name}")
            except Exception as e:
                print(f"Error during cleanup {name}: {e}")

        # Call final cleanup callback
        if self.config.on_cleanup:
            if asyncio.iscoroutinefunction(self.config.on_cleanup):
                await self.config.on_cleanup()
            else:
                self.config.on_cleanup()

        self._phase = ShutdownPhase.COMPLETED
        self._shutdown_event.set()
        print("Shutdown complete")

    async def wait(self) -> None:
        """Wait for shutdown to complete."""
        await self._shutdown_event.wait()

    @property
    def phase(self) -> ShutdownPhase:
        """Get current shutdown phase."""
        return self._phase

    @property
    def is_shutting_down(self) -> bool:
        """Check if shutdown is in progress."""
        return self._phase in (
            ShutdownPhase.DRAINING,
            ShutdownPhase.STOPPING,
        )


# Context manager for application lifecycle
class Application:
    """Context manager for application lifecycle.

    Usage:
        async with Application() as app:
            # Application is running
            await app.run()
        # Automatic cleanup on exit
    """

    def __init__(self, shutdown_config: Optional[ShutdownConfig] = None):
        """Initialize application.

        Args:
            shutdown_config: Shutdown configuration.
        """
        self.shutdown_manager = ShutdownManager(shutdown_config)
        self._running = False

    async def __aenter__(self) -> "Application":
        """Enter application context."""
        await self.shutdown_manager.start()
        self._running = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit application context and cleanup."""
        self._running = False
        if exc_type is not None:
            # Unexpected error - still try to shutdown gracefully
            await self.shutdown_manager.shutdown(reason=f"Error: {exc_val}")
        else:
            await self.shutdown_manager.shutdown(reason="Normal exit")

    async def run(self) -> None:
        """Run the application (to be overridden)."""
        while self._running:
            await asyncio.sleep(1)

    def stop(self) -> None:
        """Stop the application."""
        self._running = False


# Global shutdown manager
_shutdown_manager: Optional[ShutdownManager] = None


def get_shutdown_manager(config: Optional[ShutdownConfig] = None) -> ShutdownManager:
    """Get or create the global shutdown manager.

    Args:
        config: Shutdown configuration.

    Returns:
        Global ShutdownManager instance.
    """
    global _shutdown_manager
    if _shutdown_manager is None:
        _shutdown_manager = ShutdownManager(config)
    return _shutdown_manager
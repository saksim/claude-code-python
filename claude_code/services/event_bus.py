"""Event Bus for Claude Code Python.

Provides event-driven architecture for decoupled service communication.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import uuid

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """Event priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


@dataclass
class Event:
    """Base event class.

    Attributes:
        id: Unique event ID.
        type: Event type/name.
        payload: Event data.
        timestamp: Event creation timestamp.
        correlation_id: For distributed tracing.
        source: Event source.
        metadata: Additional metadata.
    """

    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    type: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    source: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class EventHandler:
    """Event handler wrapper."""

    def __init__(
        self,
        handler: Callable[[Event], Any],
        priority: EventPriority = EventPriority.NORMAL,
        filter_fn: Optional[Callable[[Event], bool]] = None,
    ) -> None:
        self.handler = handler
        self.priority = priority
        self.filter_fn = filter_fn
        self.call_count: int = 0

    async def handle(self, event: Event) -> Any:
        """Handle an event."""
        if self.filter_fn and not self.filter_fn(event):
            return None

        self.call_count += 1

        if asyncio.iscoroutinefunction(self.handler):
            return await self.handler(event)
        return self.handler(event)


class EventBus:
    """Central event bus for publish-subscribe pattern.

    Features:
    - Topic-based subscription
    - Priority handling
    - Event filtering
    - Async handlers
    - Dead letter queue

    Usage:
        event_bus = EventBus()

        # Subscribe to events
        async def on_tool_execute(event):
            logger.debug(f"Tool executed: {event.payload}")

        event_bus.subscribe("tool.execute", on_tool_execute)

        # Publish events
        await event_bus.publish(Event(type="tool.execute", payload={"tool": "bash"}))
    """

    def __init__(self, max_queue_size: int = 1000) -> None:
        """Initialize the event bus.

        Args:
            max_queue_size: Maximum size for event queue.
        """
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._global_handlers: List[EventHandler] = []
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None
        self._dead_letter: List[Event] = []
        self._lock = asyncio.Lock()
        
        # Statistics
        self._stats = {
            "published": 0,
            "handled": 0,
            "failed": 0,
            "dead_lettered": 0,
        }

    async def start(self) -> None:
        """Start the event bus processor."""
        if self._running:
            return

        self._running = True
        self._processor_task = asyncio.create_task(self._process_events())
        
    async def stop(self) -> None:
        """Stop the event bus processor."""
        self._running = False
        
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass

    async def _process_events(self) -> None:
        """Process events from the queue."""
        while self._running:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self._dispatch_event(event)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._stats["failed"] += 1
                logger.error(f"Error processing event: {e}")

    async def _dispatch_event(self, event: Event) -> None:
        """Dispatch an event to all handlers."""
        # Global handlers (receive all events)
        for handler in self._global_handlers:
            try:
                await handler.handle(event)
                self._stats["handled"] += 1
            except Exception as e:
                self._stats["failed"] += 1
                await self._handle_dead_letter(event, e)

        # Topic-specific handlers
        handlers = self._handlers.get(event.type, [])
        
        # Sort by priority (high first)
        handlers.sort(key=lambda h: h.priority.value)
        
        for handler in handlers:
            try:
                await handler.handle(event)
                self._stats["handled"] += 1
            except Exception as e:
                self._stats["failed"] += 1
                await self._handle_dead_letter(event, e)

    async def _handle_dead_letter(self, event: Event, error: Exception) -> None:
        """Handle dead letter events."""
        event.metadata["error"] = str(error)
        self._dead_letter.append(event)
        self._stats["dead_lettered"] += 1
        
        # Keep only last 100 dead letters
        if len(self._dead_letter) > 100:
            self._dead_letter = self._dead_letter[-100:]

    async def publish(self, event: Event) -> None:
        """Publish an event to the bus.

        Args:
            event: Event to publish.
        """
        self._stats["published"] += 1
        
        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            self._stats["failed"] += 1
            raise RuntimeError("Event queue is full")

    def subscribe(
        self,
        topic: str,
        handler: Callable[[Event], Any],
        priority: EventPriority = EventPriority.NORMAL,
        filter_fn: Optional[Callable[[Event], bool]] = None,
    ) -> Callable[[], None]:
        """Subscribe to a topic.

        Args:
            topic: Event topic to subscribe to.
            handler: Handler function.
            priority: Handler priority.
            filter_fn: Optional filter function.

        Returns:
            Unsubscribe function.
        """
        event_handler = EventHandler(handler, priority, filter_fn)
        
        if topic not in self._handlers:
            self._handlers[topic] = []
        
        self._handlers[topic].append(event_handler)
        
        def unsubscribe() -> None:
            if topic in self._handlers and event_handler in self._handlers[topic]:
                self._handlers[topic].remove(event_handler)
        
        return unsubscribe

    def subscribe_all(
        self,
        handler: Callable[[Event], Any],
        priority: EventPriority = EventPriority.NORMAL,
        filter_fn: Optional[Callable[[Event], bool]] = None,
    ) -> Callable[[], None]:
        """Subscribe to all events.

        Args:
            handler: Handler function.
            priority: Handler priority.
            filter_fn: Optional filter function.

        Returns:
            Unsubscribe function.
        """
        event_handler = EventHandler(handler, priority, filter_fn)
        self._global_handlers.append(event_handler)
        
        def unsubscribe() -> None:
            if event_handler in self._global_handlers:
                self._global_handlers.remove(event_handler)
        
        return unsubscribe

    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics.

        Returns:
            Statistics dictionary.
        """
        return {
            **self._stats,
            "queue_size": self._queue.qsize(),
            "topics": len(self._handlers),
            "global_handlers": len(self._global_handlers),
            "dead_letter_count": len(self._dead_letter),
        }

    def get_dead_letter(self, limit: int = 10) -> List[Event]:
        """Get dead letter events.

        Args:
            limit: Maximum number to return.

        Returns:
            List of dead letter events.
        """
        return self._dead_letter[-limit:]


# Global event bus
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get or create the global event bus.

    Returns:
        Global EventBus instance.
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def set_event_bus(bus: EventBus) -> None:
    """Set the global event bus.

    Args:
        bus: EventBus to use globally.
    """
    global _event_bus
    _event_bus = bus


# Convenience decorators
def on_event(
    topic: str,
    priority: EventPriority = EventPriority.NORMAL,
) -> Callable[[Callable[[Event], Any]], Callable[[Event], Any]]:
    """Decorator to subscribe to events.

    Args:
        topic: Event topic.
        priority: Handler priority.

    Returns:
        Decorated function.

    Usage:
        @on_event("tool.execute")
        async def handle_tool_execute(event):
            logger.debug(f"Tool: {event.payload}")
    """
    def decorator(handler: Callable[[Event], Any]) -> Callable[[Event], Any]:
        get_event_bus().subscribe(topic, handler, priority)
        return handler
    return decorator


def on_all_events(
    priority: EventPriority = EventPriority.NORMAL,
) -> Callable[[Callable[[Event], Any]], Callable[[Event], Any]]:
    """Decorator to subscribe to all events.

    Args:
        priority: Handler priority.

    Returns:
        Decorated function.

    Usage:
        @on_all_events()
        async def handle_all(event):
            logger.debug(f"Event: {event.type}")
    """
    def decorator(handler: Callable[[Event], Any]) -> Callable[[Event], Any]:
        get_event_bus().subscribe_all(handler, priority)
        return handler
    return decorator


# Predefined event types for Claude Code
class ToolEvents:
    """Tool-related events."""

    EXECUTED = "tool.executed"
    EXECUTING = "tool.executing"
    SUCCESS = "tool.success"
    FAILED = "tool.failed"
    APPROVAL_REQUIRED = "tool.approval_required"


class APIEvents:
    """API-related events."""

    REQUEST = "api.request"
    RESPONSE = "api.response"
    ERROR = "api.error"
    RATE_LIMITED = "api.rate_limited"


class SystemEvents:
    """System events."""

    STARTUP = "system.startup"
    SHUTDOWN = "system.shutdown"
    ERROR = "system.error"
    HEALTH_CHANGED = "system.health_changed"
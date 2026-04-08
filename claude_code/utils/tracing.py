"""Distributed Tracing for Claude Code Python.

Provides OpenTelemetry integration for observability.
"""

import contextvars
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

# For now, implement a lightweight tracing system
# Full OpenTelemetry can be added as optional dependency


class SpanKind(Enum):
    """Span kind types."""

    INTERNAL = "internal"
    CLIENT = "client"
    SERVER = "server"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class SpanStatus(Enum):
    """Span status."""

    OK = "ok"
    ERROR = "error"


@dataclass
class Span:
    """Represents a trace span."""

    name: str
    trace_id: str
    span_id: str
    parent_id: Optional[str] = None
    kind: SpanKind = SpanKind.INTERNAL
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    status: SpanStatus = SpanStatus.OK
    error_message: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: list = field(default_factory=list)

    def set_attribute(self, key: str, value: Any) -> None:
        """Set span attribute."""
        self.attributes[key] = value

    def set_status(self, status: SpanStatus, message: Optional[str] = None) -> None:
        """Set span status."""
        self.status = status
        if message:
            self.error_message = message

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add span event."""
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {},
        })

    def end(self) -> None:
        """End the span."""
        self.end_time = time.time()

    @property
    def duration_ms(self) -> Optional[float]:
        """Get duration in milliseconds."""
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return None


# Context variables for trace propagation
_current_span_var: contextvars.ContextVar[Optional[Span]] = contextvars.ContextVar(
    "current_span", default=None
)
_trace_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "trace_id", default=None
)


class Tracer:
    """Lightweight tracer for distributed tracing.

    Features:
    - Span creation and management
    - Context propagation
    - Basic sampling
    - Export handlers (can be extended for OpenTelemetry)
    """

    def __init__(self, service_name: str = "claude-code"):
        """Initialize the tracer.

        Args:
            service_name: Name of the service for trace context.
        """
        self.service_name = service_name
        self._spans: List[Span] = []
        self._export_handler: Optional[Callable[[List[Span]], None]] = None

    def start_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Span:
        """Start a new span.

        Args:
            name: Span name.
            kind: Span kind.
            attributes: Initial attributes.

        Returns:
            New Span instance.
        """
        # Get or create trace ID
        trace_id = _trace_id_var.get()
        if not trace_id:
            trace_id = self._generate_trace_id()
            _trace_id_var.set(trace_id)

        # Get parent span
        parent_span = _current_span_var.get()

        span = Span(
            name=name,
            trace_id=trace_id,
            span_id=self._generate_span_id(),
            parent_id=parent_span.span_id if parent_span else None,
            kind=kind,
            attributes=attributes or {},
        )

        return span

    def enter(self, span: Span) -> Span:
        """Enter a span context (for 'with' statement)."""
        _current_span_var.set(span)
        self._spans.append(span)
        return span

    def exit(self, span: Span, exc: Optional[Exception] = None) -> None:
        """Exit a span context."""
        span.end()
        if exc:
            span.set_status(SpanStatus.ERROR, str(exc))

        # Call export handler if set
        if self._export_handler:
            self._export_handler([span])

        # Restore parent context
        _current_span_var.set(None)

    def set_export_handler(self, handler: Callable[[List[Span]], None]) -> None:
        """Set handler for span export."""
        self._export_handler = handler

    @staticmethod
    def _generate_trace_id() -> str:
        """Generate a unique trace ID."""
        return uuid.uuid4().hex

    @staticmethod
    def _generate_span_id() -> str:
        """Generate a unique span ID."""
        return uuid.uuid4().hex[:16]

    def get_current_span(self) -> Optional[Span]:
        """Get the current active span."""
        return _current_span_var.get()

    def get_trace_id(self) -> Optional[str]:
        """Get the current trace ID."""
        return _trace_id_var.get()


# Context manager for span lifecycle
class span:
    """Context manager for creating and managing spans.

    Usage:
        tracer = Tracer("my-service")
        with tracer.start_span("operation") as span:
            span.set_attribute("key", "value")
            # ... do work
    """

    def __init__(self, tracer: Tracer, name: str, **kwargs: Any):
        self.tracer = tracer
        self.name = name
        self.kwargs = kwargs
        self.span: Optional[Span] = None

    def __enter__(self) -> Span:
        self.span = self.tracer.start_span(self.name, **self.kwargs)
        self.tracer.enter(self.span)
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.tracer.exit(self.span, exc_val)


# Global tracer instance
_tracer: Optional[Tracer] = None


def get_tracer(service_name: str = "claude-code") -> Tracer:
    """Get or create the global tracer.

    Args:
        service_name: Name of the service.

    Returns:
        Global Tracer instance.
    """
    global _tracer
    if _tracer is None:
        _tracer = Tracer(service_name)
    return _tracer


def set_tracer(tracer: Tracer) -> None:
    """Set the global tracer.

    Args:
        tracer: Tracer instance to use globally.
    """
    global _tracer
    _tracer = tracer


def get_current_trace_id() -> Optional[str]:
    """Get the current trace ID.

    Returns:
        Current trace ID or None.
    """
    return _trace_id_var.get()


def get_current_span() -> Optional[Span]:
    """Get the current span.

    Returns:
        Current Span or None.
    """
    return _current_span_var.get()


# Decorator for automatic tracing
def traced(
    name: Optional[str] = None,
    kind: SpanKind = SpanKind.INTERNAL,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to automatically trace function calls.

    Args:
        name: Optional span name (defaults to function name).
        kind: Span kind.

    Returns:
        Decorated function with tracing.

    Usage:
        @traced()
        async def my_function():
            ...
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        span_name = name or func.__name__
        tracer = get_tracer()

        async def async_wrapper(*args: Any, **kwargs: Any):
            with tracer.start_span(span_name, kind=kind) as span:
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("result.type", type(result).__name__)
                    return result
                except Exception as e:
                    span.set_status(SpanStatus.ERROR, str(e))
                    span.add_event("exception", {"type": type(e).__name__, "message": str(e)})
                    raise

        def sync_wrapper(*args: Any, **kwargs: Any):
            with tracer.start_span(span_name, kind=kind) as span:
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("result.type", type(result).__name__)
                    return result
                except Exception as e:
                    span.set_status(SpanStatus.ERROR, str(e))
                    span.add_event("exception", {"type": type(e).__name__, "message": str(e)})
                    raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# Integration point for OpenTelemetry (future)
class OpenTelemetryIntegration:
    """Placeholder for OpenTelemetry integration.

    This can be expanded to use opentelemetry-sdk when needed.
    """

    @staticmethod
    def setup_tracer_provider(service_name: str) -> Any:
        """Setup OpenTelemetry tracer provider.

        Requires: pip install opentelemetry-api opentelemetry-sdk
        """
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry.sdk.resources import Resource

            resource = Resource.create({"service.name": service_name})
            provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(provider)

            return provider
        except ImportError:
            return None

    @staticmethod
    def add_console_exporter() -> None:
        """Add console span exporter for debugging."""
        try:
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter
            from opentelemetry import trace

            trace.get_tracer_provider().add_span_processor(
                BatchSpanProcessor(ConsoleSpanExporter())
            )
        except ImportError:
            pass
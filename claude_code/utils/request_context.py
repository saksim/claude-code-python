"""Request Context Manager for Claude Code Python.

Provides request ID and correlation ID propagation across the application.
"""

import contextvars
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple


# Context variables for request-level data
request_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id", default=None
)
correlation_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "correlation_id", default=None
)
request_context_var: contextvars.ContextVar[Dict[str, Any]] = contextvars.ContextVar(
    "request_context", default=None
)


def generate_request_id() -> str:
    """Generate a unique request ID.

    Returns:
        UUID-based request ID.
    """
    return uuid.uuid4().hex


def generate_correlation_id() -> str:
    """Generate a unique correlation ID.

    Returns:
        UUID-based correlation ID for distributed tracing.
    """
    return uuid.uuid4().hex


class RequestContext:
    """Container for request-level context data.

    Attributes:
        request_id: Unique identifier for this request.
        correlation_id: ID for distributed tracing across services.
        metadata: Additional request-specific data.
    """

    def __init__(
        self,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        self.request_id = request_id or generate_request_id()
        self.correlation_id = correlation_id or generate_correlation_id()
        self.metadata: Dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        """Set a metadata value.

        Args:
            key: Metadata key.
            value: Metadata value.
        """
        self.metadata[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a metadata value.

        Args:
            key: Metadata key.
            default: Default value if not found.

        Returns:
            Metadata value or default.
        """
        return self.metadata.get(key, default)

    def update(self, data: Dict[str, Any]) -> None:
        """Update multiple metadata values.

        Args:
            data: Dictionary of metadata to update.
        """
        self.metadata.update(data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
        }


class RequestContextManager:
    """Manager for request context lifecycle.

    Usage:
        async with RequestContextManager() as ctx:
            # Context is active
            get_request_id()  # Returns the request ID
            set_request_metadata("user_id", "123")

        # Context is automatically cleaned up
    """

    def __init__(self, request_id: Optional[str] = None, correlation_id: Optional[str] = None):
        """Initialize context manager.

        Args:
            request_id: Optional pre-generated request ID.
            correlation_id: Optional pre-generated correlation ID.
        """
        self.request_id = request_id or generate_request_id()
        self.correlation_id = correlation_id or generate_correlation_id()
        self._context = RequestContext(self.request_id, self.correlation_id)

    async def __aenter__(self) -> RequestContext:
        """Enter context and set variables."""
        request_id_var.set(self.request_id)
        correlation_id_var.set(self.correlation_id)
        request_context_var.set(self._context.metadata)
        return self._context

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context and clear variables."""
        request_id_var.set(None)
        correlation_id_var.set(None)
        request_context_var.set(None)


def get_request_id() -> Optional[str]:
    """Get the current request ID.

    Returns:
        Current request ID or None if not in request context.
    """
    return request_id_var.get()


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID.

    Returns:
        Current correlation ID or None if not in request context.
    """
    return correlation_id_var.get()


def get_request_metadata(key: str, default: Any = None) -> Any:
    """Get a request metadata value.

    Args:
        key: Metadata key.
        default: Default value if not found.

    Returns:
        Metadata value or default.
    """
    context = request_context_var.get()
    if context:
        return context.get(key, default)
    return default


def set_request_metadata(key: str, value: Any) -> None:
    """Set a request metadata value.

    Args:
        key: Metadata key.
        value: Metadata value.
    """
    context = request_context_var.get()
    if context is not None:
        context[key] = value


def clear_request_context() -> None:
    """Clear the current request context."""
    request_id_var.set(None)
    correlation_id_var.set(None)
    request_context_var.set(None)


def copy_request_context() -> Dict[str, Optional[str]]:
    """Copy current request context.

    Returns:
        Dictionary with request_id and correlation_id.
    """
    return {
        "request_id": request_id_var.get(),
        "correlation_id": correlation_id_var.get(),
    }


# Decorator for automatic request context
def with_request_context(
    request_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> Callable:
    """Decorator to wrap function in request context.

    Args:
        request_id: Optional request ID (generated if not provided).
        correlation_id: Optional correlation ID (generated if not provided).

    Returns:
        Decorated function with request context.

    Usage:
        @with_request_context()
        async def my_function():
            request_id = get_request_id()
            ...
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            ctx_request_id = request_id or generate_request_id()
            ctx_correlation_id = correlation_id or generate_correlation_id()
            async with RequestContextManager(ctx_request_id, ctx_correlation_id):
                return await func(*args, **kwargs)

        def sync_wrapper(*args, **kwargs):
            ctx_request_id = request_id or generate_request_id()
            ctx_correlation_id = correlation_id or generate_correlation_id()

            # For sync functions, use context vars directly
            token1 = request_id_var.set(ctx_request_id)
            token2 = correlation_id_var.set(ctx_correlation_id)
            token3 = request_context_var.set({})
            try:
                return func(*args, **kwargs)
            finally:
                request_id_var.reset(token1)
                correlation_id_var.reset(token2)
                request_context_var.reset(token3)

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# HTTP headers for request context propagation
REQUEST_ID_HEADER = "X-Request-ID"
CORRELATION_ID_HEADER = "X-Correlation-ID"


def extract_request_context_from_headers(
    headers: Dict[str, str],
) -> Tuple[Optional[str], Optional[str]]:
    """Extract request IDs from HTTP headers.

    Args:
        headers: HTTP headers dictionary.

    Returns:
        Tuple of (request_id, correlation_id).
    """
    request_id = headers.get(REQUEST_ID_HEADER)
    correlation_id = headers.get(CORRELATION_ID_HEADER)
    return request_id, correlation_id


def inject_request_context_into_headers(
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """Inject request IDs into HTTP headers.

    Args:
        headers: Optional existing headers dict.

    Returns:
        Headers with request context.
    """
    if headers is None:
        headers = {}

    request_id = get_request_id()
    correlation_id = get_correlation_id()

    if request_id:
        headers[REQUEST_ID_HEADER] = request_id
    if correlation_id:
        headers[CORRELATION_ID_HEADER] = correlation_id

    return headers
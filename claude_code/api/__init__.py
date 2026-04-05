"""
API client module for Claude Code Python.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Re-exports for clean imports
"""

from claude_code.api.client import (
    APIClient,
    APIClientConfig,
    APIProvider,
    MessageParam,
    QueryOptions,
    StreamEvent,
    APIClientError,
    RateLimitError,
    AuthenticationError,
    ContextLengthError,
    APIRetryableError,
    RetryConfig,
    with_retry,
)

__all__ = [
    "APIClient",
    "APIClientConfig",
    "APIProvider",
    "MessageParam",
    "QueryOptions",
    "StreamEvent",
    "APIClientError",
    "RateLimitError",
    "AuthenticationError",
    "ContextLengthError",
    "APIRetryableError",
    "RetryConfig",
    "with_retry",
]

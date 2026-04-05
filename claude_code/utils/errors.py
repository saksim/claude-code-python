"""Error handling utilities for Claude Code Python."""

from __future__ import annotations

import traceback
from dataclasses import dataclass, field
from typing import Any


class ClaudeCodeError(Exception):
    """Base exception for Claude Code errors.

    Attributes:
        message: The error message.
        code: Optional error code for programmatic handling.
    """

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code


class AbortError(ClaudeCodeError):
    """Operation was aborted."""

    pass


class RateLimitError(ClaudeCodeError):
    """Rate limit exceeded."""

    pass


class AuthenticationError(ClaudeCodeError):
    """Authentication failed."""

    pass


class ContextLengthError(ClaudeCodeError):
    """Context too long."""

    pass


class PermissionError(ClaudeCodeError):
    """Permission denied."""

    pass


class ValidationError(ClaudeCodeError):
    """Input validation failed."""

    pass


class ToolError(ClaudeCodeError):
    """Tool execution error.

    Attributes:
        message: The error message.
        tool_name: Name of the tool that caused the error.
        code: Optional error code.
    """

    def __init__(
        self,
        message: str,
        tool_name: str = "",
        code: str | None = None,
    ) -> None:
        super().__init__(message, code)
        self.tool_name = tool_name


class SessionError(ClaudeCodeError):
    """Session-related error."""

    pass


class ConfigurationError(ClaudeCodeError):
    """Configuration error."""

    pass


class NetworkError(ClaudeCodeError):
    """Network-related error."""

    pass


@dataclass(frozen=True, slots=True)
class ErrorContext:
    """Context for an error.

    Attributes:
        tool_name: Name of the tool that was executing.
        message_id: ID of the message being processed.
        session_id: ID of the current session.
        additional_info: Additional error context.
    """

    tool_name: str | None = None
    message_id: str | None = None
    session_id: str | None = None
    additional_info: dict[str, Any] = field(default_factory=dict)


def get_error_message(error: Exception) -> str:
    """Get a user-friendly error message.

    Args:
        error: The exception to extract message from.

    Returns:
        A string representation of the error.
    """
    if isinstance(error, ClaudeCodeError):
        return str(error)
    return str(error)


def is_retryable_error(error: Exception) -> bool:
    """Check if an error is retryable.

    Args:
        error: The exception to check.

    Returns:
        True if the operation can be retried.
    """
    if isinstance(error, RateLimitError):
        return True
    if isinstance(error, NetworkError):
        return True
    return False


def format_error(error: Exception, include_traceback: bool = False) -> str:
    """Format an error for display.

    Args:
        error: The exception to format.
        include_traceback: Whether to include the traceback.

    Returns:
        Formatted error string.
    """
    message = get_error_message(error)

    if include_traceback:
        tb = traceback.format_exception(type(error), error, error.__traceback__)
        return f"{message}\n\nTraceback:\n{''.join(tb)}"

    return message
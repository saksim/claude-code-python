"""Error handling utilities for Claude Code Python."""

from __future__ import annotations

import logging
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


class ToolNotFoundError(ToolError):
    """Tool not found in registry."""
    
    def __init__(self, tool_name: str) -> None:
        super().__init__(
            message=f"Tool '{tool_name}' not found",
            tool_name=tool_name,
            code="TOOL_NOT_FOUND"
        )


class ToolExecutionError(ToolError):
    """Tool execution failed."""
    
    def __init__(self, message: str, tool_name: str = "", cause: Exception | None = None) -> None:
        super().__init__(message, tool_name, "TOOL_EXECUTION_ERROR")
        self.cause = cause


class ToolTimeoutError(ToolError):
    """Tool execution timed out."""
    
    def __init__(self, tool_name: str, timeout_seconds: int) -> None:
        super().__init__(
            message=f"Tool '{tool_name}' timed out after {timeout_seconds}s",
            tool_name=tool_name,
            code="TOOL_TIMEOUT"
        )


class ToolValidationError(ToolError):
    """Tool input validation failed."""
    
    def __init__(self, message: str, tool_name: str = "", field: str = "") -> None:
        super().__init__(message, tool_name, "TOOL_VALIDATION_ERROR")
        self.field = field


class ToolPermissionError(ToolError):
    """Tool permission denied."""
    
    def __init__(self, message: str, tool_name: str = "") -> None:
        super().__init__(message, tool_name, "TOOL_PERMISSION_DENIED")


class ToolResultError(ToolError):
    """Tool returned an error result."""
    
    def __init__(self, message: str, tool_name: str = "", is_error: bool = True) -> None:
        super().__init__(message, tool_name, "TOOL_RESULT_ERROR")
        self.is_error = is_error


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


class ToolErrorHandler:
    """统一的工具错误处理器.
    
    提供统一的错误处理和日志记录.
    
    Example:
        >>> handler = ToolErrorHandler()
        >>> result = handler.handle(error, context)
    """
    
    def __init__(self) -> None:
        """Initialize error handler."""
        self._logger = logging.getLogger(__name__)
    
    def handle(
        self,
        error: Exception,
        tool_name: str = "",
        context: dict[str, Any] | None = None,
    ) -> "ToolResult":
        """Handle tool error and return error result.
        
        Args:
            error: The exception to handle
            tool_name: Name of the tool that threw the error
            context: Additional context information
            
        Returns:
            ToolResult with error information
        """
        from claude_code.tools.base import ToolResult
        
        # Log error
        self._log_error(error, tool_name, context)
        
        # Map to appropriate error type
        if isinstance(error, ToolError):
            return ToolResult(
                content=error.message,
                is_error=True,
                error_code=error.code,
            )
        
        # Generic error handling
        error_type = type(error).__name__
        return ToolResult(
            content=str(error),
            is_error=True,
            error_code=error_type,
        )
    
    def _log_error(
        self,
        error: Exception,
        tool_name: str,
        context: dict[str, Any] | None,
    ) -> None:
        """Log error with appropriate level."""
        if isinstance(error, ToolTimeoutError):
            self._logger.warning(
                f"Tool timeout: {tool_name}",
                extra={"error": str(error), "context": context}
            )
        elif isinstance(error, ToolPermissionError):
            self._logger.warning(
                f"Tool permission denied: {tool_name}",
                extra={"error": str(error), "context": context}
            )
        elif isinstance(error, ToolValidationError):
            self._logger.info(
                f"Tool validation error: {tool_name}",
                extra={"error": str(error), "context": context}
            )
        else:
            self._logger.error(
                f"Tool execution error: {tool_name}",
                extra={"error": str(error), "context": context},
                exc_info=True
            )


# 默认错误处理器实例
default_tool_error_handler = ToolErrorHandler()


__all__ = [
    # Base
    "ClaudeCodeError",
    # Tool errors
    "ToolError",
    "ToolNotFoundError",
    "ToolExecutionError",
    "ToolTimeoutError",
    "ToolValidationError",
    "ToolPermissionError",
    "ToolResultError",
    # Other errors
    "AbortError",
    "RateLimitError",
    "AuthenticationError",
    "ContextLengthError",
    "PermissionError",
    "ValidationError",
    "SessionError",
    "ConfigurationError",
    "NetworkError",
    # Context
    "ErrorContext",
    # Utilities
    "get_error_message",
    "is_retryable_error",
    "format_error",
    "ToolErrorHandler",
    "default_tool_error_handler",
]
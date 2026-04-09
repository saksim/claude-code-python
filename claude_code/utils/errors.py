"""Error handling utilities for Claude Code Python."""

import logging
import traceback
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ClaudeCodeError(Exception):
    """Base exception for Claude Code errors.

    Attributes:
        message: The error message.
        code: Optional error code for programmatic handling.
    """

    def __init__(self, message: str, code: Optional[str] = None) -> None:
        super().__init__(message)
        self.code = code


class AbortError(ClaudeCodeError):
    """Operation was aborted."""

    pass


class RateLimitError(ClaudeCodeError):
    """Rate limit exceeded."""

    def __init__(self, message: str, retry_after: Optional[float] = None) -> None:
        super().__init__(message, code="RATE_LIMIT")
        self.retry_after = retry_after


class AuthenticationError(ClaudeCodeError):
    """Authentication failed."""

    pass


class PermissionError(ClaudeCodeError):
    """Permission denied."""

    pass


class ContextLengthError(ClaudeCodeError):
    """Context length exceeded."""

    pass


class ValidationError(ClaudeCodeError):
    """Validation failed."""

    pass


class ToolError(ClaudeCodeError):
    """Tool execution error."""

    pass


class SessionError(ClaudeCodeError):
    """Session-related error."""

    pass


class ConfigurationError(ClaudeCodeError):
    """Configuration error."""

    pass


class NetworkError(ClaudeCodeError):
    """Network-related error."""

    pass


class ShellError(ClaudeCodeError):
    """Shell command execution error.
    
    Attributes:
        stdout: Standard output from the command
        stderr: Standard error from the command
        code: Exit code from the command
        interrupted: Whether the command was interrupted
    """

    def __init__(
        self,
        message: str,
        stdout: str = "",
        stderr: str = "",
        code: int = 0,
        interrupted: bool = False,
    ) -> None:
        super().__init__(message, code="SHELL_ERROR")
        self.stdout = stdout
        self.stderr = stderr
        self.code = code
        self.interrupted = interrupted


class TelemetrySafeError(ClaudeCodeError):
    """Error with a message safe for telemetry.
    
    Use when you need an error message that doesn't contain sensitive data
    like file paths, URLs, or code snippets.
    
    Attributes:
        telemetry_message: Sanitized message for telemetry/logging
    """

    def __init__(self, message: str, telemetry_message: Optional[str] = None) -> None:
        super().__init__(message, code="TELEMETRY_SAFE")
        self.telemetry_message = telemetry_message or message


class ToolExecutionError(ClaudeCodeError):
    """Tool execution failed.

    Attributes:
        tool_name: Name of the tool that failed.
        input_data: Input that was provided to the tool.
    """

    def __init__(
        self,
        message: str,
        tool_name: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, code="TOOL_ERROR")
        self.tool_name = tool_name
        self.input_data = input_data


class ContextError(ClaudeCodeError):
    """Context-related error."""

    pass


class APIError(ClaudeCodeError):
    """API communication error.

    Attributes:
        status_code: HTTP status code if available.
        response: Optional response data.
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, code="API_ERROR")
        self.status_code = status_code
        self.response = response


# Error utility functions

def to_error(e: Any) -> Exception:
    """Normalize an unknown value into an Error.
    
    Use at catch-site boundaries when you need an Error instance.
    
    Args:
        e: Unknown error value
        
    Returns:
        Normalized Exception
    """
    if isinstance(e, Exception):
        return e
    return Exception(str(e))


def error_message(e: Any) -> str:
    """Extract a string message from an unknown error-like value.
    
    Use when you only need the message (e.g., for logging or display).
    
    Args:
        e: Error-like value
        
    Returns:
        Error message string
    """
    if isinstance(e, Exception):
        return e.message if hasattr(e, 'message') else str(e)
    return str(e)


def get_errno_code(e: Any) -> Optional[str]:
    """Extract the errno code (e.g., 'ENOENT', 'EACCES') from a caught error.
    
    Returns None if the error has no code or is not an ErrnoException.
    
    Args:
        e: Error-like value
        
    Returns:
        Errno code string or None
    """
    if isinstance(e, OSError):
        return e.code
    if isinstance(e, Exception) and hasattr(e, 'code'):
        code = e.code
        if isinstance(code, str):
            return code
    return None


def is_enoent(e: Any) -> bool:
    """True if the error means the path is missing, inaccessible, or 
    structurally unreachable.
    
    Covers: ENOENT, ENOTDIR, ELOOP, ENOENT
    
    Args:
        e: Error-like value
        
    Returns:
        True if it's a "not found" error
    """
    code = get_errno_code(e)
    if code is None:
        return False
    return code in ('ENOENT', 'ENOTDIR', 'ELOOP')


def get_errno_path(e: Any) -> Optional[str]:
    """Extract the errno path (the filesystem path that triggered the error)
    from a caught error.
    
    Args:
        e: Error-like value
        
    Returns:
        Path string or None
    """
    if isinstance(e, OSError):
        return e.filename
    if isinstance(e, Exception) and hasattr(e, 'path'):
        path = e.path
        if isinstance(path, str):
            return path
    return None


def short_error_stack(e: Any, max_frames: int = 5) -> str:
    """Extract error message + top N stack frames from an unknown error.
    
    Use when the error flows to the model as a tool_result — full stack
    traces are ~500-2000 chars of mostly-irrelevant internal frames and
    waste context tokens. Keep the full stack in debug logs instead.
    
    Args:
        e: Error-like value
        max_frames: Maximum number of stack frames to include
        
    Returns:
        Shortened error string
    """
    if not isinstance(e, Exception):
        return str(e)
    
    if not e.args:
        return e.message if hasattr(e, 'message') else str(e)
    
    # Get the message from args
    message = e.args[0] if e.args else (e.message if hasattr(e, 'message') else str(e))
    
    # Get stack trace if available
    if not e.__traceback__:
        return message if isinstance(message, str) else str(message)
    
    # Format limited stack trace
    import traceback
    stack_lines = traceback.format_tb(e.__traceback__, limit=max_frames)
    frames = [line.strip() for line in stack_lines if 'File' in line]
    
    if len(frames) <= max_frames:
        return f"{message}\n" + "".join(stack_lines)
    
    header = f"{type(e).__name__}: {message}"
    return header + "\n" + "\n".join(frames[:max_frames])


def has_exact_error_message(e: Any, message: str) -> bool:
    """Check if error has exact message.
    
    Args:
        e: Error-like value
        message: Expected message
        
    Returns:
        True if messages match exactly
    """
    if isinstance(e, Exception):
        return e.message == message
    return False


def is_retryable_error(error: Exception) -> bool:
    """Check if an error is retryable.

    Args:
        error: The exception to check.

    Returns:
        True if the operation should be retried.
    """
    retryable_types = (
        RateLimitError,
        ConnectionError,
        TimeoutError,
    )

    # Check if it's a retryable type
    if isinstance(error, retryable_types):
        return True

    # Check for retryable messages
    error_str = str(error).lower()
    retryable_patterns = [
        "timeout",
        "connection",
        "temporary",
        "unavailable",
    ]

    return any(pattern in error_str for pattern in retryable_patterns)


@dataclass
class ErrorContext:
    """Context information for an error.

    Attributes:
        error_type: Type of error.
        message: Error message.
        stack_trace: Optional stack trace.
        metadata: Additional context data.
    """

    error_type: str
    message: str
    stack_trace: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolErrorHandler:
    """Handler for tool execution errors.

    Provides consistent error handling and recovery strategies.
    """

    def __init__(self) -> None:
        """Initialize the error handler."""
        self._error_counts: Dict[str, int] = {}
        self._error_history: List[ErrorContext] = []

    def handle_error(self, error: Exception, tool_name: str) -> ErrorContext:
        """Handle a tool execution error.

        Args:
            error: The exception that occurred.
            tool_name: Name of the tool that failed.

        Returns:
            ErrorContext with error details.
        """
        # Track error counts
        if tool_name not in self._error_counts:
            self._error_counts[tool_name] = 0
        self._error_counts[tool_name] += 1

        # Create error context
        context = ErrorContext(
            error_type=type(error).__name__,
            message=str(error),
            stack_trace=traceback.format_exc(),
            metadata={"tool_name": tool_name, "count": self._error_counts[tool_name]},
        )

        self._error_history.append(context)

        # Keep only last 100 errors
        if len(self._error_history) > 100:
            self._error_history = self._error_history[-100:]

        # Log the error
        logger = logging.getLogger(__name__)
        logger.error(
            "Tool error: %s in %s: %s",
            context.error_type,
            tool_name,
            context.message,
        )

        return context

    def get_error_count(self, tool_name: str) -> int:
        """Get error count for a tool.

        Args:
            tool_name: Name of the tool.

        Returns:
            Number of errors for the tool.
        """
        return self._error_counts.get(tool_name, 0)

    def get_recent_errors(self, limit: int = 10) -> List[ErrorContext]:
        """Get recent errors.

        Args:
            limit: Maximum number of errors to return.

        Returns:
            List of recent error contexts.
        """
        return self._error_history[-limit:]

    def reset_errors(self, tool_name: Optional[str] = None) -> None:
        """Reset error tracking.

        Args:
            tool_name: Optional tool name to reset. If None, reset all.
        """
        if tool_name:
            self._error_counts.pop(tool_name, None)
        else:
            self._error_counts.clear()
            self._error_history.clear()


def format_error(error: Exception, include_traceback: bool = False) -> str:
    """Format an exception for display.

    Args:
        error: The exception to format.
        include_traceback: Whether to include the traceback.

    Returns:
        Formatted error string.
    """
    lines = [
        f"{type(error).__name__}: {str(error)}",
    ]

    if include_traceback:
        lines.append("")
        lines.append("Traceback:")
        lines.append(traceback.format_exc())

    return "\n".join(lines)


def get_error_message(error: Exception) -> str:
    """Get a user-friendly error message.

    Args:
        error: The exception.

    Returns:
        User-friendly error message.
    """
    if hasattr(error, "message"):
        return error.message
    return str(error)


__all__ = [
    "ClaudeCodeError",
    "AbortError",
    "RateLimitError",
    "AuthenticationError",
    "PermissionError",
    "ContextLengthError",
    "ValidationError",
    "ToolError",
    "SessionError",
    "ConfigurationError",
    "NetworkError",
    "ShellError",
    "TelemetrySafeError",
    "ToolExecutionError",
    "ContextError",
    "APIError",
    "to_error",
    "error_message",
    "get_errno_code",
    "is_enoent",
    "get_errno_path",
    "short_error_stack",
    "has_exact_error_message",
    "is_retryable_error",
    "ErrorContext",
    "ToolErrorHandler",
    "format_error",
    "get_error_message",
]
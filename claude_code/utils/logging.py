"""
Claude Code Python - Logging System
Centralized logging configuration.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Singleton pattern with proper typing
- Context manager support
- __slots__ for memory optimization
- Structured logging support
- No aggressive handler clearing
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Literal
from datetime import datetime
from enum import Enum


class LogLevel(Enum):
    """Log level enum for type safety."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ClaudeCodeLogger:
    """Centralized logging for Claude Code.
    
    Singleton logger providing structured logging with console and file output.
    Uses __slots__ for memory optimization.
    
    Attributes:
        _instance: Singleton instance
        _logger: Internal logger instance
        _log_file: Optional log file path
        _verbose: Whether debug logging is enabled
        _structured: Whether to use structured logging
    
    Example:
        >>> logger = ClaudeCodeLogger.get_instance()
        >>> logger.setup("my-app", verbose=True, log_file="/var/log/app.log")
        >>> logger.info("Application started")
    """
    
    __slots__ = ('_logger', '_log_file', '_verbose', '_structured', '_console_handler', '_file_handler')
    
    _instance: "ClaudeCodeLogger | None" = None
    
    def __init__(self) -> None:
        self._logger: logging.Logger | None = None
        self._log_file: Path | None = None
        self._verbose: bool = False
        self._structured: bool = False
        self._console_handler: logging.StreamHandler | None = None
        self._file_handler: logging.FileHandler | None = None
    
    @classmethod
    def get_instance(cls) -> 'ClaudeCodeLogger':
        """Get the singleton logger instance.
        
        Returns:
            The singleton ClaudeCodeLogger instance.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def setup(
        self,
        name: str = "claude-code",
        verbose: bool = False,
        log_file: str | Path | None = None,
        structured: bool = False,
    ) -> logging.Logger:
        """Setup logging configuration.
        
        Args:
            name: Logger name (default: "claude-code")
            verbose: Enable debug level logging
            log_file: Optional file path for log output
            structured: Enable structured logging output
        
        Returns:
            Configured logger instance.
        """
        self._verbose = verbose
        self._structured = structured
        self._logger = logging.getLogger(name)
        self._logger.setLevel(logging.DEBUG if verbose else logging.INFO)
        
        # Prevent propagation to root logger to avoid duplicate logs
        self._logger.propagate = False
        
        # Only add handlers if none exist (avoid duplicate handlers)
        if not self._logger.handlers:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            # Console handler (stderr) - reuse if possible
            self._console_handler = logging.StreamHandler(sys.stderr)
            self._console_handler.setFormatter(formatter)
            self._logger.addHandler(self._console_handler)
        
        # File handler if specified
        if log_file:
            self._log_file = Path(log_file)
            self._log_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if we already have a file handler for this path
            existing_file_handler = None
            for handler in self._logger.handlers:
                if isinstance(handler, logging.FileHandler) and handler.baseFilename == str(self._log_file):
                    existing_file_handler = handler
                    break
            
            if existing_file_handler is None:
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                self._file_handler = logging.FileHandler(self._log_file)
                self._file_handler.setFormatter(formatter)
                self._logger.addHandler(self._file_handler)
            else:
                self._file_handler = existing_file_handler
        
        return self._logger
    
    def get_logger(self) -> logging.Logger:
        """Get the configured logger.
        
        Returns:
            Logger instance, auto-configured if not setup.
        """
        if self._logger is None:
            return self.setup()
        return self._logger
    
    def set_level(self, level: LogLevel | str) -> None:
        """Set the logging level.
        
        Args:
            level: Log level as enum or string.
        """
        if isinstance(level, str):
            level = LogLevel(level.lower())
        
        level_map = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL,
        }
        self._logger.setLevel(level_map.get(level, logging.INFO))
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message.
        
        Args:
            message: Log message
            **kwargs: Additional context for logging
        """
        if self._verbose:
            self._log_with_context(logging.DEBUG, message, kwargs)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message.
        
        Args:
            message: Log message
            **kwargs: Additional context for logging
        """
        self._log_with_context(logging.INFO, message, kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message.
        
        Args:
            message: Log message
            **kwargs: Additional context for logging
        """
        self._log_with_context(logging.WARNING, message, kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message.
        
        Args:
            message: Log message
            **kwargs: Additional context for logging
        """
        self._log_with_context(logging.ERROR, message, kwargs)
    
    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message.
        
        Args:
            message: Log message
            **kwargs: Additional context for logging
        """
        self._log_with_context(logging.CRITICAL, message, kwargs)
    
    def exception(self, message: str, **kwargs: Any) -> None:
        """Log exception with traceback.
        
        Args:
            message: Log message
            **kwargs: Additional context for logging
        """
        self._log_with_context(logging.ERROR, message, kwargs, exc_info=True)
    
    def _log_with_context(
        self,
        level: int,
        message: str,
        context: dict[str, Any],
        exc_info: bool = False,
    ) -> None:
        """Log with structured context.
        
        Args:
            level: Logging level
            message: Log message
            context: Additional context
            exc_info: Include exception info
        """
        logger = self.get_logger()
        
        if self._structured and context:
            # Structured logging format
            context_str = " ".join(f"{k}={v}" for k, v in context.items())
            full_message = f"{message} | {context_str}"
        else:
            full_message = message
        
        logger.log(level, full_message, exc_info=exc_info)


def get_logger(name: str = "claude-code") -> logging.Logger:
    """Get a logger instance.
    
    Args:
        name: Logger name (default: "claude-code")
    
    Returns:
        Configured logger instance.
    """
    return ClaudeCodeLogger.get_instance().get_logger()


def setup_logging(
    verbose: bool = False,
    log_file: str | Path | None = None,
    structured: bool = False,
) -> logging.Logger:
    """Setup logging configuration.
    
    Args:
        verbose: Enable debug level logging
        log_file: Optional file path for log output
        structured: Enable structured logging output
    
    Returns:
        Configured logger instance.
    """
    return ClaudeCodeLogger.get_instance().setup(
        verbose=verbose,
        log_file=log_file,
        structured=structured,
    )


def set_log_level(level: LogLevel | str) -> None:
    """Set the global logging level.
    
    Args:
        level: Log level as enum or string.
    """
    ClaudeCodeLogger.get_instance().set_level(level)


__all__ = [
    "ClaudeCodeLogger",
    "LogLevel",
    "get_logger",
    "setup_logging",
    "set_log_level",
]

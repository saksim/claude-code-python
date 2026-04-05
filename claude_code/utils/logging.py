"""
Claude Code Python - Logging System
Centralized logging configuration.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Singleton pattern with proper typing
- Context manager support
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional, Any
from datetime import datetime


class ClaudeCodeLogger:
    """Centralized logging for Claude Code.
    
    Singleton logger providing structured logging with console and file output.
    
    Attributes:
        _instance: Singleton instance
        _logger: Internal logger instance
        _log_file: Optional log file path
        _verbose: Whether debug logging is enabled
    
    Example:
        >>> logger = ClaudeCodeLogger.get_instance()
        >>> logger.setup("my-app", verbose=True, log_file="/var/log/app.log")
        >>> logger.info("Application started")
    """
    
    _instance: Optional['ClaudeCodeLogger'] = None
    
    def __init__(self) -> None:
        self._logger: Optional[logging.Logger] = None
        self._log_file: Optional[Path] = None
        self._verbose: bool = False
    
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
        log_file: Optional[str] = None,
    ) -> logging.Logger:
        """Setup logging configuration.
        
        Args:
            name: Logger name (default: "claude-code")
            verbose: Enable debug level logging
            log_file: Optional file path for log output
        
        Returns:
            Configured logger instance.
        """
        self._verbose = verbose
        self._logger = logging.getLogger(name)
        self._logger.setLevel(logging.DEBUG if verbose else logging.INFO)
        
        # Avoid duplicate handlers
        if self._logger.handlers:
            self._logger.handlers.clear()
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler (stderr)
        console = logging.StreamHandler(sys.stderr)
        console.setFormatter(formatter)
        self._logger.addHandler(console)
        
        # File handler if specified
        if log_file:
            self._log_file = Path(log_file)
            self._log_file.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(self._log_file)
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)
        
        return self._logger
    
    def get_logger(self) -> logging.Logger:
        """Get the configured logger.
        
        Returns:
            Logger instance, auto-configured if not setup.
        """
        if self._logger is None:
            return self.setup()
        return self._logger
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message.
        
        Args:
            message: Log message
            **kwargs: Additional context for logging
        """
        if self._verbose:
            self.get_logger().debug(message, **kwargs)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message.
        
        Args:
            message: Log message
            **kwargs: Additional context for logging
        """
        self.get_logger().info(message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message.
        
        Args:
            message: Log message
            **kwargs: Additional context for logging
        """
        self.get_logger().warning(message, **kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message.
        
        Args:
            message: Log message
            **kwargs: Additional context for logging
        """
        self.get_logger().error(message, **kwargs)
    
    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message.
        
        Args:
            message: Log message
            **kwargs: Additional context for logging
        """
        self.get_logger().critical(message, **kwargs)
    
    def exception(self, message: str, **kwargs: Any) -> None:
        """Log exception with traceback.
        
        Args:
            message: Log message
            **kwargs: Additional context for logging
        """
        self.get_logger().exception(message, **kwargs)


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
    log_file: Optional[str] = None,
) -> logging.Logger:
    """Setup logging configuration.
    
    Args:
        verbose: Enable debug level logging
        log_file: Optional file path for log output
    
    Returns:
        Configured logger instance.
    """
    return ClaudeCodeLogger.get_instance().setup(verbose=verbose, log_file=log_file)


__all__ = [
    "ClaudeCodeLogger",
    "get_logger",
    "setup_logging",
]

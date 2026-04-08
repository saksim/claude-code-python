"""Claude Code Python - Unified Logging System
统一日志系统，支持结构化日志、多种输出、级别控制.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Context managers for logging
- Structured logging
"""

import logging
import sys
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager


class LogLevel(Enum):
    """日志级别."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(Enum):
    """日志格式."""
    TEXT = "text"
    JSON = "json"
    SIMPLE = "simple"


@dataclass(frozen=True)
class LogEntry:
    """日志条目."""
    timestamp: str
    level: str
    logger: str
    message: str
    extra: Dict[str, Any] = field(default_factory=dict)


class ClaudeCodeLogger:
    """Claude Code 统一日志器.
    
    Features:
    - 结构化日志支持
    - 多种输出格式 (text, json, simple)
    - 上下文管理器支持
    - 日志级别控制
    - 文件输出支持
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("User logged in", user_id="123")
        >>> with logger.context(request_id="abc"):
        ...     logger.info("Processing request")
    """
    
    _instances: Dict[str, "ClaudeCodeLogger"] = {}
    _default_handler: Optional[logging.Handler] = None
    
    def __init__(
        self,
        name: str,
        level: str = "INFO",
        format_type: LogFormat = LogFormat.TEXT,
        log_file: Optional[str] = None,
    ) -> None:
        """初始化日志器.
        
        Args:
            name: 日志器名称
            level: 日志级别
            format_type: 输出格式
            log_file: 可选的文件输出路径
        """
        self.name = name
        self.level = getattr(logging, level.upper())
        self.format_type = format_type
        self._context: Dict[str, Any] = {}
        self._file_handler: Optional[logging.FileHandler] = None
        
        # Create logger
        self._logger = logging.getLogger(name)
        self._logger.setLevel(self.level)
        self._logger.handlers.clear()
        
        # Add console handler
        self._setup_console_handler()
        
        # Add file handler if specified
        if log_file:
            self._setup_file_handler(log_file)
    
    def _setup_console_handler(self) -> None:
        """设置控制台处理器."""
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(self.level)
        
        if self.format_type == LogFormat.JSON:
            formatter = logging.Formatter('%(message)s')
        elif self.format_type == LogFormat.SIMPLE:
            formatter = logging.Formatter('%(levelname)s: %(message)s')
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)
    
    def _setup_file_handler(self, log_file: str) -> None:
        """设置文件处理器."""
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        self._file_handler = logging.FileHandler(log_file)
        self._file_handler.setLevel(self.level)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self._file_handler.setFormatter(formatter)
        self._logger.addHandler(self._file_handler)
    
    @contextmanager
    def context(self, **kwargs: Any) -> Any:
        """上下文管理器 - 为日志添加上下文信息.
        
        Example:
            >>> logger = get_logger(__name__)
            >>> with logger.context(request_id="123", user_id="456"):
            ...     logger.info("Processing request")
        """
        old_context = self._context.copy()
        self._context.update(kwargs)
        try:
            yield self
        finally:
            self._context = old_context
    
    def _format_message(self, level: str, message: str) -> str:
        """格式化日志消息."""
        if self.format_type == LogFormat.JSON:
            log_data = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "level": level,
                "logger": self.name,
                "message": message,
                **self._context
            }
            return json.dumps(log_data)
        return message
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Debug 级别日志."""
        self._logger.debug(self._format_message("DEBUG", message), extra=kwargs or self._context)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Info 级别日志."""
        self._logger.info(self._format_message("INFO", message), extra=kwargs or self._context)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Warning 级别日志."""
        self._logger.warning(self._format_message("WARNING", message), extra=kwargs or self._context)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Error 级别日志."""
        self._logger.error(self._format_message("ERROR", message), extra=kwargs or self._context)
    
    def critical(self, message: str, **kwargs: Any) -> None:
        """Critical 级别日志."""
        self._logger.critical(self._format_message("CRITICAL", message), extra=kwargs or self._context)
    
    def exception(self, message: str, **kwargs: Any) -> None:
        """Exception 日志 (自动包含堆栈跟踪)."""
        self._logger.exception(self._format_message("ERROR", message), extra=kwargs or self._context)
    
    def set_level(self, level: str) -> None:
        """设置日志级别."""
        self.level = getattr(logging, level.upper())
        self._logger.setLevel(self.level)


# 全局日志配置
_loggers: Dict[str, ClaudeCodeLogger] = {}
_default_level = "INFO"
_default_format = LogFormat.TEXT


def configure_logging(
    level: str = "INFO",
    format_type: LogFormat = LogFormat.TEXT,
    log_file: Optional[str] = None,
    log_dir: Optional[str] = None,
) -> None:
    """配置全局日志系统.
    
    Args:
        level: 默认日志级别
        format_type: 输出格式
        log_file: 全局日志文件路径
        log_dir: 日志目录 (会自动创建 claude.log)
    """
    global _default_level, _default_format
    
    _default_level = level
    _default_format = format_type
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.handlers.clear()
    
    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(getattr(logging, level.upper()))
    
    if format_type == LogFormat.JSON:
        formatter = logging.Formatter('%(message)s')
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console.setFormatter(formatter)
    root_logger.addHandler(console)
    
    # File handler if specified
    if log_file or log_dir:
        log_path = log_file or (Path(log_dir or "~/.claude/logs") / "claude.log")
        path = Path(log_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(path)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str, level: Optional[str] = None) -> ClaudeCodeLogger:
    """获取日志器实例.
    
    Args:
        name: 日志器名称 (通常使用 __name__)
        level: 可选的日志级别覆盖
        
    Returns:
        ClaudeCodeLogger 实例
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started")
    """
    if name not in _loggers:
        _loggers[name] = ClaudeCodeLogger(
            name=name,
            level=level or _default_level,
            format_type=_default_format,
        )
    return _loggers[name]


def get_root_logger() -> logging.Logger:
    """获取根日志器."""
    return logging.getLogger("claude_code")


# 便捷函数
def log_debug(message: str, **kwargs: Any) -> None:
    """快捷 debug 日志."""
    get_logger("claude_code").debug(message, **kwargs)


def log_info(message: str, **kwargs: Any) -> None:
    """快捷 info 日志."""
    get_logger("claude_code").info(message, **kwargs)


def log_warning(message: str, **kwargs: Any) -> None:
    """快捷 warning 日志."""
    get_logger("claude_code").warning(message, **kwargs)


def log_error(message: str, **kwargs: Any) -> None:
    """快捷 error 日志."""
    get_logger("claude_code").error(message, **kwargs)


def log_exception(message: str, **kwargs: Any) -> None:
    """快捷 exception 日志."""
    get_logger("claude_code").exception(message, **kwargs)


__all__ = [
    "ClaudeCodeLogger",
    "LogLevel",
    "LogFormat",
    "LogEntry",
    "configure_logging",
    "get_logger",
    "get_root_logger",
    "log_debug",
    "log_info",
    "log_warning",
    "log_error",
    "log_exception",
]
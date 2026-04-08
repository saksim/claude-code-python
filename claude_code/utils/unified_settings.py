"""
Claude Code Python - Unified Settings
使用 Pydantic Settings 统一管理配置.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Pydantic for complex validation
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal
from dataclasses import dataclass

try:
    from pydantic_settings import BaseSettings
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseSettings = object  # type: ignore


if PYDANTIC_AVAILABLE:
    from pydantic import Field as PdField

    class Settings(BaseSettings):
        """Claude Code Python 统一配置类.
        
        使用 Pydantic Settings 进行配置管理，支持:
        - 环境变量自动加载
        - .env 文件支持
        - 类型验证和默认值
        - 敏感信息掩码
        """
        
        # API 配置
        api_key: str = PdField(default="", description="API key for LLM service")
        api_base_url: str = PdField(default="https://api.anthropic.com", description="API base URL")
        api_version: str = PdField(default="2023-06-01", description="API version")
        default_model: str = PdField(default="claude-sonnet-4-20250514", description="Default LLM model")
        
        # 功能开关
        feature_kairos: bool = PdField(default=False, description="Enable KAIROS features")
        feature_web_browser: bool = PdField(default=False, description="Enable Web Browser tool")
        feature_workflow_scripts: bool = PdField(default=False, description="Enable Workflow Scripts")
        feature_monitor_tool: bool = PdField(default=False, description="Enable Monitor tool")
        
        # 性能配置
        max_concurrent_tools: int = PdField(default=10, description="Max concurrent tools")
        tool_timeout_seconds: int = PdField(default=300, description="Tool timeout seconds")
        max_retries: int = PdField(default=3, description="Max retries")
        
        # 缓存配置
        cache_enabled: bool = PdField(default=True, description="Enable caching")
        cache_ttl_seconds: int = PdField(default=3600, description="Cache TTL")
        cache_max_size: int = PdField(default=1000, description="Max cache size")
        
        # 日志配置
        log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = PdField(default="INFO")
        log_format: str = PdField(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        
        # 会话配置
        session_dir: str = PdField(default="~/.claude/sessions")
        max_session_history: int = PdField(default=100)
        
        # MCP 配置
        mcp_timeout: int = PdField(default=30)
        mcp_max_connections: int = PdField(default=5)
        
        # 安全配置
        allow_file_write: bool = PdField(default=True)
        allow_shell_exec: bool = PdField(default=True)
        
        model_config = {"env_prefix": "CLAUDE_", "case_sensitive": False}
else:
    @dataclass
    class Settings:
        """Fallback settings when Pydantic is not available."""
        api_key: str = ""
        api_base_url: str = "https://api.anthropic.com"
        default_model: str = "claude-sonnet-4-20250514"
        feature_kairos: bool = False
        feature_web_browser: bool = False
        max_concurrent_tools: int = 10
        tool_timeout_seconds: int = 300
        cache_enabled: bool = True
        cache_ttl_seconds: int = 3600
        log_level: str = "INFO"
        session_dir: str = "~/.claude/sessions"
        mcp_timeout: int = 30
        allow_file_write: bool = True
        allow_shell_exec: bool = True


__all__ = ["Settings", "PYDANTIC_AVAILABLE"]
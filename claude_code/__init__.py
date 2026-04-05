"""
Claude Code Python - Package initialization
"""

from claude_code.api.client import APIClient, APIClientConfig, APIProvider
from claude_code.engine.query import QueryEngine, QueryConfig, Message, ToolUse
from claude_code.engine.context import ContextBuilder, GitInfo, ClaudeMdLoader, PermissionMode
from claude_code.engine.session import Session, SessionManager, SessionStore
from claude_code.tools.registry import create_default_registry, ToolRegistry
from claude_code.repl import REPL, REPLConfig, PipeMode
from claude_code.config import Config, get_config, LocalSettings
from claude_code.services.mcp import MCPClient, MCPManager

__version__ = "1.0.0"

__all__ = [
    "APIClient",
    "APIClientConfig", 
    "APIProvider",
    "QueryEngine",
    "QueryConfig",
    "Message",
    "ToolUse",
    "ContextBuilder",
    "GitInfo",
    "ClaudeMdLoader",
    "PermissionMode",
    "Session",
    "SessionManager",
    "SessionStore",
    "create_default_registry",
    "ToolRegistry",
    "REPL",
    "REPLConfig",
    "PipeMode",
    "Config",
    "get_config",
    "LocalSettings",
    "MCPClient",
    "MCPManager",
]

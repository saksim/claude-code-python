"""Claude Code Python package exports.

Exports are resolved lazily to reduce cold-start import cost.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

__version__ = "1.0.0"

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    "APIClient": ("claude_code.api.client", "APIClient"),
    "APIClientConfig": ("claude_code.api.client", "APIClientConfig"),
    "APIProvider": ("claude_code.api.client", "APIProvider"),
    "QueryEngine": ("claude_code.engine.query", "QueryEngine"),
    "QueryConfig": ("claude_code.engine.query", "QueryConfig"),
    "Message": ("claude_code.engine.query", "Message"),
    "ToolUse": ("claude_code.engine.query", "ToolUse"),
    "ContextBuilder": ("claude_code.engine.context", "ContextBuilder"),
    "GitInfo": ("claude_code.engine.context", "GitInfo"),
    "ClaudeMdLoader": ("claude_code.engine.context", "ClaudeMdLoader"),
    "PermissionMode": ("claude_code.permissions", "PermissionMode"),
    "Session": ("claude_code.engine.session", "Session"),
    "SessionManager": ("claude_code.engine.session", "SessionManager"),
    "SessionStore": ("claude_code.engine.session", "SessionStore"),
    "create_default_registry": ("claude_code.tools.registry", "create_default_registry"),
    "ToolRegistry": ("claude_code.tools.registry", "ToolRegistry"),
    "REPL": ("claude_code.repl", "REPL"),
    "REPLConfig": ("claude_code.repl", "REPLConfig"),
    "PipeMode": ("claude_code.repl", "PipeMode"),
    "Config": ("claude_code.config", "Config"),
    "get_config": ("claude_code.config", "get_config"),
    "LocalSettings": ("claude_code.config", "LocalSettings"),
    "MCPClient": ("claude_code.services.mcp", "MCPClient"),
    "MCPManager": ("claude_code.services.mcp", "MCPManager"),
}

__all__ = list(_LAZY_EXPORTS.keys())


def __getattr__(name: str) -> Any:
    if name not in _LAZY_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, attr_name = _LAZY_EXPORTS[name]
    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + __all__)

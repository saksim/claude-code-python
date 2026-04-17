"""Deprecated tool registry shim.

This module is kept for backward compatibility and proxies to
`claude_code.tools.registry`.
"""

from __future__ import annotations

import warnings
from typing import Any

from claude_code.tools.base import Tool
from claude_code.tools.registry import ToolRegistry as _ToolRegistry
from claude_code.tools.registry import create_default_registry as _create_default_registry

warnings.warn(
    f"{__name__} is deprecated and will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)

# Compatibility placeholder. The real registry lives in claude_code.tools.registry.
TOOL_REGISTRY: dict[str, tuple[str, str]] = {}


class LazyToolRegistry(_ToolRegistry):
    """Backward-compatible alias to the canonical ToolRegistry."""

    @property
    def loaded_count(self) -> int:
        return len([tool for tool in self._tools.values() if tool is not None])

    @property
    def available_count(self) -> int:
        return len(self._tools)


class ToolRegistry(LazyToolRegistry):
    """Legacy alias."""


def create_default_registry(force_eager: bool = False) -> LazyToolRegistry:
    """Create default registry, optionally preloading all tools."""
    registry = _create_default_registry()
    if force_eager:
        registry.preload()

    return registry  # type: ignore[return-value]


def create_default_registry_old() -> ToolRegistry:
    """Legacy eager-loading constructor."""
    return create_default_registry(force_eager=True)


__all__ = [
    "LazyToolRegistry",
    "ToolRegistry",
    "create_default_registry",
    "create_default_registry_old",
    "TOOL_REGISTRY",
    "Tool",
]

"""
Claude Code Python - Unified Permission System

This module is the single source of truth for permission types.
All other modules must import PermissionMode from here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum


class PermissionMode(Enum):
    """Permission modes for tool execution.
    
    Single canonical definition — all modules import from here.
    """
    DEFAULT = "default"
    AUTO = "auto"
    PLAN = "plan"
    ACCEPT_EDITS = "acceptEdits"
    BYPASS = "bypass"
    YOLO = "yolo"


# PermissionMode string values for validation
PERMISSION_MODES: list[str] = [m.value for m in PermissionMode]

_SAFE_READ_TOOLS: frozenset[str] = frozenset({"read", "glob", "grep", "web_search", "web_fetch"})
_PLAN_ALLOWED_TOOLS: frozenset[str] = frozenset({"read", "glob", "grep", "web_search", "web_fetch"})
_ACCEPT_EDITS_ALLOWED_TOOLS: frozenset[str] = frozenset(
    {"read", "glob", "grep", "web_search", "web_fetch", "write", "edit", "notebook_edit"}
)
_STRICT_DENY_TOOLS: frozenset[str] = frozenset(
    {"bash", "powershell", "write", "edit", "notebook_edit", "rm", "delete", "task_create", "agent"}
)
_STRICT_ALLOW_TOOLS: frozenset[str] = frozenset({"read", "glob", "grep"})
_STRICT_DENY_PREFIXES: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PermissionEvaluation:
    """Structured permission decision for runtime audit and diagnostics."""

    tool_name: str
    allowed: bool
    reason: str


@dataclass(frozen=True, slots=True)
class ToolPermissionContext:
    """Simplified permission context following Claw design.
    
    Using frozen=True, slots=True for immutability and memory efficiency.
    
    Attributes:
        deny_names: Frozen set of denied tool names
        deny_prefixes: Tuple of denied tool name prefixes
        allow_names: Frozen set of allowed tool names
        allow_prefixes: Tuple of allowed tool name prefixes
    """
    deny_names: frozenset[str] = field(default_factory=frozenset)
    deny_prefixes: tuple[str, ...] = ()
    allow_names: frozenset[str] = field(default_factory=frozenset)
    allow_prefixes: tuple[str, ...] = ()
    default_allow: bool = True
    
    def blocks(self, tool_name: str) -> bool:
        """Check if tool execution should be blocked.
        
        Args:
            tool_name: Name of the tool to check
            
        Returns:
            True if tool should be blocked
        """
        return not self.evaluate(tool_name).allowed
    
    def allows(self, tool_name: str) -> bool:
        """Check if tool execution is allowed.
        
        Args:
            tool_name: Name of the tool to check
            
        Returns:
            True if tool is allowed
        """
        return self.evaluate(tool_name).allowed

    def evaluate(self, tool_name: str) -> PermissionEvaluation:
        """Return structured allow/deny decision with reason."""
        lowered = tool_name.lower()

        if lowered in self.deny_names:
            return PermissionEvaluation(tool_name=tool_name, allowed=False, reason="deny_name")

        for prefix in self.deny_prefixes:
            if lowered.startswith(prefix.lower()):
                return PermissionEvaluation(tool_name=tool_name, allowed=False, reason="deny_prefix")

        if lowered in self.allow_names:
            return PermissionEvaluation(tool_name=tool_name, allowed=True, reason="allow_name")

        for prefix in self.allow_prefixes:
            if lowered.startswith(prefix.lower()):
                return PermissionEvaluation(tool_name=tool_name, allowed=True, reason="allow_prefix")

        return PermissionEvaluation(
            tool_name=tool_name,
            allowed=bool(self.default_allow),
            reason="default_allow" if self.default_allow else "default_deny",
        )
    
    @classmethod
    def from_rules(
        cls,
        always_allow: Optional[list[str]] = None,
        always_deny: Optional[list[str]] = None,
    ) -> "ToolPermissionContext":
        """Create permission context from rule lists.
        
        Args:
            always_allow: List of tool names to always allow
            always_deny: List of tool names to always deny
            
        Returns:
            Configured ToolPermissionContext instance
        """
        allow_names_set: set[str] = set()
        deny_names_set: set[str] = set()
        allow_prefixes_list: list[str] = []
        deny_prefixes_list: list[str] = []
        
        for item in (always_allow or []):
            lowered = item.lower()
            if lowered.endswith("*"):
                allow_prefixes_list.append(lowered[:-1])
            else:
                allow_names_set.add(lowered)
        for item in (always_deny or []):
            lowered = item.lower()
            if lowered.endswith("*"):
                deny_prefixes_list.append(lowered[:-1])
            else:
                deny_names_set.add(lowered)
        
        return cls(
            deny_names=frozenset(deny_names_set),
            deny_prefixes=tuple(deny_prefixes_list),
            allow_names=frozenset(allow_names_set),
            allow_prefixes=tuple(allow_prefixes_list),
            default_allow=True,
        )
    
    @classmethod
    def default(cls) -> "ToolPermissionContext":
        """Default permission context - allows all tools.
        
        Returns:
            PermissionContext that allows all tools
        """
        return cls(
            deny_names=frozenset(),
            deny_prefixes=(),
            allow_names=frozenset(),
            allow_prefixes=(),
            default_allow=True,
        )
    
    @classmethod
    def strict(cls) -> "ToolPermissionContext":
        """Strict mode - blocks dangerous tools by default.
        
        Returns:
            PermissionContext with strict restrictions
        """
        return cls(
            deny_names=_STRICT_DENY_TOOLS,
            deny_prefixes=_STRICT_DENY_PREFIXES,
            allow_names=_STRICT_ALLOW_TOOLS,
            allow_prefixes=(),
            default_allow=True,
        )
    
    @classmethod
    def allow_only(cls, allow_names: list[str]) -> "ToolPermissionContext":
        """Create a context that blocks everything except explicit allow list."""
        return cls(
            deny_names=frozenset(),
            deny_prefixes=(),
            allow_names=frozenset(a.lower() for a in allow_names),
            allow_prefixes=(),
            default_allow=False,
        )


class PermissionChecker:
    """Permission checker using simplified permission context.
    
    Provides methods to check if tools can be executed based on
    the permission context rules.
    
    Attributes:
        context: Current permission context
    
    Example:
        >>> checker = PermissionChecker()
        >>> if checker.can_execute("read"):
        ...     print("Read allowed")
    """
    
    def __init__(self, context: Optional[ToolPermissionContext] = None):
        self._context = context or ToolPermissionContext.default()
    
    @property
    def context(self) -> ToolPermissionContext:
        """Get current permission context."""
        return self._context
    
    def set_context(self, context: ToolPermissionContext) -> None:
        """Set new permission context.
        
        Args:
            context: New permission context to use
        """
        self._context = context
    
    def can_execute(self, tool_name: str) -> bool:
        """Check if tool execution is allowed.
        
        Args:
            tool_name: Name of the tool to check
            
        Returns:
            True if tool is allowed to execute
        """
        return self.evaluate(tool_name).allowed

    def evaluate(self, tool_name: str) -> PermissionEvaluation:
        """Return structured permission decision for a tool."""
        return self._context.evaluate(tool_name)
    
    def check_or_raise(self, tool_name: str) -> None:
        """Check permission, raise exception if not allowed.
        
        Args:
            tool_name: Name of the tool to check
            
        Raises:
            PermissionError: If tool is not allowed
        """
        if not self.can_execute(tool_name):
            raise PermissionError(f"Tool '{tool_name}' is not allowed by permission context")
    
    def filter_tools(self, tool_names: list[str]) -> list[str]:
        """Filter tool list to only allowed tools.
        
        Args:
            tool_names: List of tool names to filter
            
        Returns:
            List of tool names that are allowed
        """
        return [name for name in tool_names if self.can_execute(name)]


def create_permission_checker(
    mode: str | PermissionMode = "default",
    always_allow: Optional[list[str]] = None,
    always_deny: Optional[list[str]] = None,
) -> PermissionChecker:
    """Create a permission checker with specified mode.
    
    Args:
        mode: Permission mode ("default", "strict", "auto", "bypass")
        always_allow: List of tools to always allow
        always_deny: List of tools to always deny
        
    Returns:
        Configured PermissionChecker instance
    
    Raises:
        ValueError: If mode is not recognized
    """
    mode_value = (mode.value if isinstance(mode, PermissionMode) else str(mode)).strip()
    mode_normalized = mode_value.lower()
    
    if mode_normalized == "yolo":
        context = ToolPermissionContext.default()
    elif mode_normalized == "bypass":
        context = ToolPermissionContext.default()
    elif mode_normalized == "default":
        context = ToolPermissionContext.from_rules(
            always_allow=always_allow or [],
            always_deny=always_deny or [],
        )
    elif mode_normalized == "strict":
        context = ToolPermissionContext.strict()
    elif mode_normalized == "auto":
        allowed = sorted(_SAFE_READ_TOOLS.union(set(a.lower() for a in (always_allow or []))))
        context = ToolPermissionContext.allow_only(allowed)
    elif mode_normalized == "plan":
        allowed = sorted(_PLAN_ALLOWED_TOOLS.union(set(a.lower() for a in (always_allow or []))))
        context = ToolPermissionContext.allow_only(allowed)
    elif mode_normalized == "acceptedits":
        allowed = sorted(_ACCEPT_EDITS_ALLOWED_TOOLS.union(set(a.lower() for a in (always_allow or []))))
        context = ToolPermissionContext.allow_only(allowed)
    else:
        context = ToolPermissionContext.from_rules(
            always_allow=always_allow or [],
            always_deny=always_deny or [],
        )
    
    return PermissionChecker(context)


__all__ = [
    "PermissionMode",
    "PERMISSION_MODES",
    "PermissionEvaluation",
    "ToolPermissionContext",
    "PermissionChecker",
    "create_permission_checker",
]

"""
Claude Code Python - Simplified Permission Context
Provides a simplified permission system for tool execution control.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Dataclass patterns (frozen/slots)
- frozenset for constant sets
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


# Module-level constants
_STRICT_DENY_TOOLS: frozenset[str] = frozenset({"bash", "powershell", "shell", "exec", "run"})
_STRICT_ALLOW_TOOLS: frozenset[str] = frozenset({"read", "glob", "grep", "lsp"})
_STRICT_DENY_PREFIXES: tuple[str, ...] = ("mcp_",)
_AUTO_ALLOW_TOOLS: list[str] = ["read", "glob", "grep"]


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
    
    def blocks(self, tool_name: str) -> bool:
        """Check if tool execution should be blocked.
        
        Args:
            tool_name: Name of the tool to check
            
        Returns:
            True if tool should be blocked
        """
        lowered = tool_name.lower()
        
        # Check allow list first
        if lowered in self.allow_names:
            return False
        
        for prefix in self.allow_prefixes:
            if lowered.startswith(prefix.lower()):
                return False
        
        # Check deny list
        if lowered in self.deny_names:
            return True
        
        for prefix in self.deny_prefixes:
            if lowered.startswith(prefix.lower()):
                return True
        
        return False
    
    def allows(self, tool_name: str) -> bool:
        """Check if tool execution is allowed.
        
        Args:
            tool_name: Name of the tool to check
            
        Returns:
            True if tool is allowed
        """
        return not self.blocks(tool_name)
    
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
        allow_names = frozenset(a.lower() for a in (always_allow or []))
        deny_names = frozenset(d.lower() for d in (always_deny or []))
        
        allow_prefixes: tuple[str, ...] = ()
        deny_prefixes: tuple[str, ...] = ()
        
        return cls(
            deny_names=deny_names,
            deny_prefixes=deny_prefixes,
            allow_names=allow_names,
            allow_prefixes=allow_prefixes,
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
        return self._context.allows(tool_name)
    
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
    mode: str = "default",
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
    if mode == "default":
        context = ToolPermissionContext.default()
    elif mode == "strict":
        context = ToolPermissionContext.strict()
    elif mode == "auto":
        context = ToolPermissionContext.from_rules(
            always_allow=always_allow or ["read", "glob", "grep"],
            always_deny=always_deny or [],
        )
    elif mode == "bypass":
        context = ToolPermissionContext.default()
    else:
        context = ToolPermissionContext.from_rules(
            always_allow=always_allow or [],
            always_deny=always_deny or [],
        )
    
    return PermissionChecker(context)


__all__ = [
    "ToolPermissionContext",
    "PermissionChecker",
    "create_permission_checker",
]

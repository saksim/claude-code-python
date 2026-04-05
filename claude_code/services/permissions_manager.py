"""
Claude Code Python - Permissions System
Manages tool execution permissions and authorization.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Frozen dataclasses for immutable configurations
- Proper separation of concerns
"""

from __future__ import annotations

import fnmatch
import os
from typing import Any, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum


class PermissionMode(Enum):
    """Permission mode for tool execution.
    
    Attributes:
        DEFAULT: Ask for permission before each tool execution
        AUTO: Auto-approve safe operations, ask for others
        PLAN: Ask for permission for everything
        BYPASS: No permission checks (trusted environment)
        YOLO: No restrictions at all (testing only)
    """
    DEFAULT = "default"
    AUTO = "auto"
    PLAN = "plan"
    BYPASS = "bypass"
    YOLO = "yolo"


class PermissionResult(Enum):
    """Permission check result.
    
    Attributes:
        ALLOWED: Tool execution is permitted
        DENIED: Tool execution is not permitted
        ASK: User should be prompted for permission
    """
    ALLOWED = "allowed"
    DENIED = "denied"
    ASK = "ask"


@dataclass(frozen=True, slots=True)
class PermissionRule:
    """A permission rule for tool access control.
    
    Immutable rule that defines patterns for allowing or denying
    tool execution based on glob-style matching.
    
    Attributes:
        tool_pattern: Glob pattern for matching tool names
        action: Either "allow" or "deny"
        conditions: Additional conditions for the rule
    """
    tool_pattern: str
    action: str = "allow"
    conditions: dict[str, Any] = field(default_factory=dict)


@dataclass
class PermissionRequest:
    """A permission request for tool execution.
    
    Represents a request to execute a tool with associated
    input data and metadata.
    
    Attributes:
        tool_name: Name of the tool being requested
        input_data: Input parameters for the tool
        reason: Optional reason for the request
        user_id: Optional user identifier
    """
    tool_name: str
    input_data: dict[str, Any]
    reason: str = ""
    user_id: Optional[str] = None


class PermissionsManager:
    """Manages tool execution permissions.
    
    Provides fine-grained control over which tools can be executed
    and under what conditions. Supports multiple permission modes
    and custom rule configurations.
    
    Attributes:
        SAFE_TOOLS: Set of tools considered safe (auto-allowed in AUTO mode)
        DESTRUCTIVE_TOOLS: Set of tools that modify files
        EXECUTION_TOOLS: Set of tools that execute commands
    
    Example:
        >>> manager = PermissionsManager(mode=PermissionMode.AUTO)
        >>> result = manager.check("read", {"file": "/path/to/file"})
        >>> print(result)  # PermissionResult.ALLOWED
    """
    
    # Tools considered safe (auto-allowed in AUTO mode)
    SAFE_TOOLS: frozenset[str] = frozenset({
        "read", "glob", "grep", "lsp",
        "list_mcp_resources", "read_mcp_resource",
    })
    
    # Tools that modify files
    DESTRUCTIVE_TOOLS: frozenset[str] = frozenset({
        "write", "edit", "notebook_edit",
        "delete", "rm", "rmdir",
    })
    
    # Tools that execute code
    EXECUTION_TOOLS: frozenset[str] = frozenset({
        "bash", "powershell", "shell",
        "exec", "run", "npm", "pip",
    })
    
    def __init__(self, mode: PermissionMode = PermissionMode.DEFAULT) -> None:
        """Initialize permissions manager.
        
        Args:
            mode: Initial permission mode
        """
        self._mode = mode
        self._rules: list[PermissionRule] = []
        self._callback: Optional[Callable[[PermissionRequest], bool]] = None
        self._approval_cache: dict[str, bool] = {}
    
    def set_mode(self, mode: PermissionMode) -> None:
        """Set the permission mode.
        
        Args:
            mode: New permission mode to use
        """
        self._mode = mode
    
    @property
    def mode(self) -> PermissionMode:
        """Get current permission mode."""
        return self._mode
    
    def set_callback(
        self,
        callback: Callable[[PermissionRequest], bool],
    ) -> None:
        """Set callback for permission requests.
        
        The callback receives a PermissionRequest and returns True/False
        to indicate whether the tool should be allowed to execute.
        
        Args:
            callback: Function that handles permission requests
        """
        self._callback = callback
    
    def check(
        self,
        tool_name: str,
        input_data: Optional[dict[str, Any]] = None,
        reason: str = "",
    ) -> PermissionResult:
        """Check if a tool execution is allowed.
        
        Evaluates the tool against current rules and permission mode
        to determine whether to allow, deny, or ask for permission.
        
        Args:
            tool_name: Name of the tool to check
            input_data: Optional tool input parameters
            reason: Optional reason for execution
            
        Returns:
            PermissionResult indicating the decision
        """
        # Check rules first
        for rule in self._rules:
            if self._matches_pattern(tool_name, rule.tool_pattern):
                if rule.action == "deny":
                    return PermissionResult.DENIED
                if rule.action == "allow":
                    return PermissionResult.ALLOWED
        
        # Check mode
        if self._mode in (PermissionMode.BYPASS, PermissionMode.YOLO):
            return PermissionResult.ALLOWED
        
        if self._mode == PermissionMode.AUTO:
            if tool_name in self.SAFE_TOOLS:
                return PermissionResult.ALLOWED
            if tool_name in self.DESTRUCTIVE_TOOLS:
                return PermissionResult.ASK
            if tool_name in self.EXECUTION_TOOLS:
                return PermissionResult.ASK
            return PermissionResult.ALLOWED
        
        if self._mode == PermissionMode.PLAN:
            return PermissionResult.ASK
        
        # DEFAULT mode
        if tool_name in self.SAFE_TOOLS:
            cache_key = f"{tool_name}:{str(input_data)}"
            if cache_key in self._approval_cache:
                return PermissionResult.ALLOWED
            return PermissionResult.ASK
        
        return PermissionResult.ASK
    
    def approve(
        self,
        tool_name: str,
        input_data: Optional[dict[str, Any]] = None,
    ) -> None:
        """Approve a tool execution (caches approval).
        
        Args:
            tool_name: Name of the tool to approve
            input_data: Optional tool input parameters
        """
        cache_key = f"{tool_name}:{str(input_data)}"
        self._approval_cache[cache_key] = True
    
    def deny(
        self,
        tool_name: str,
        input_data: Optional[dict[str, Any]] = None,
    ) -> None:
        """Deny a tool execution.
        
        Args:
            tool_name: Name of the tool to deny
            input_data: Optional tool input parameters
        """
        cache_key = f"{tool_name}:{str(input_data)}"
        self._approval_cache[cache_key] = False
    
    def clear_cache(self) -> None:
        """Clear the approval cache."""
        self._approval_cache.clear()
    
    def add_rule(
        self,
        tool_pattern: str,
        action: str = "allow",
        conditions: Optional[dict[str, Any]] = None,
    ) -> PermissionRule:
        """Add a permission rule.
        
        Args:
            tool_pattern: Glob pattern for tool names
            action: "allow" or "deny"
            conditions: Optional additional conditions
            
        Returns:
            The created PermissionRule
        """
        rule = PermissionRule(
            tool_pattern=tool_pattern,
            action=action,
            conditions=conditions or {},
        )
        self._rules.append(rule)
        return rule
    
    def remove_rule(self, tool_pattern: str) -> bool:
        """Remove a rule by pattern.
        
        Args:
            tool_pattern: Pattern of the rule to remove
            
        Returns:
            True if rule was removed, False if not found
        """
        for i, rule in enumerate(self._rules):
            if rule.tool_pattern == tool_pattern:
                self._rules.pop(i)
                return True
        return False
    
    def _matches_pattern(self, tool_name: str, pattern: str) -> bool:
        """Check if tool name matches pattern.
        
        Args:
            tool_name: Tool name to check
            pattern: Glob pattern to match against
            
        Returns:
            True if tool matches pattern
        """
        if "*" in pattern or "?" in pattern:
            return fnmatch.fnmatch(tool_name, pattern)
        return tool_name == pattern
    
    def format_status(self) -> str:
        """Format permission status for display.
        
        Returns:
            Human-readable permission status string
        """
        lines: list[str] = [
            "Permission Mode",
            "=" * 40,
            f"Mode: {self._mode.value}",
            f"Rules: {len(self._rules)}",
            f"Cached approvals: {len(self._approval_cache)}",
            "",
            "Tool Categories:",
            f"  Safe: {', '.join(sorted(self.SAFE_TOOLS))}",
            f"  Destructive: {', '.join(sorted(self.DESTRUCTIVE_TOOLS))}",
            f"  Execution: {', '.join(sorted(self.EXECUTION_TOOLS))}",
        ]
        return "\n".join(lines)


# Global permissions manager
_permissions_manager: Optional[PermissionsManager] = None


def get_permissions_manager() -> PermissionsManager:
    """Get the global permissions manager instance.
    
    Creates a new instance if one doesn't exist, using the
    CLAUDE_PERMISSIONS environment variable for mode.
    
    Returns:
        Global PermissionsManager instance
    """
    global _permissions_manager
    if _permissions_manager is None:
        mode = os.getenv("CLAUDE_PERMISSIONS", "default")
        try:
            perm_mode = PermissionMode(mode.lower())
        except ValueError:
            perm_mode = PermissionMode.DEFAULT
        
        _permissions_manager = PermissionsManager(mode=perm_mode)
    
    return _permissions_manager

"""Compatibility wrapper for service-level permission management.

Historically this module had an independent permission policy engine. It now
wraps the canonical implementation in ``claude_code.permissions`` while keeping
legacy method signatures and enums intact.
"""

from __future__ import annotations

import os
import fnmatch
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

from claude_code.permissions import PermissionMode, create_permission_checker


class PermissionResult(Enum):
    """Permission check result."""

    ALLOWED = "allowed"
    DENIED = "denied"
    ASK = "ask"


@dataclass(frozen=True, slots=True)
class PermissionRule:
    """A compatibility permission rule."""

    tool_pattern: str
    action: str = "allow"
    conditions: dict[str, Any] = field(default_factory=dict)


@dataclass
class PermissionRequest:
    """Permission request details."""

    tool_name: str
    input_data: dict[str, Any]
    reason: str = ""
    user_id: Optional[str] = None


class PermissionsManager:
    """Service-level compatibility manager delegating to canonical checker."""

    def __init__(self, mode: PermissionMode = PermissionMode.DEFAULT) -> None:
        self._mode = mode
        self._rules: list[PermissionRule] = []
        self._callback: Optional[Callable[[PermissionRequest], bool]] = None
        self._approval_cache: dict[str, bool] = {}

    def set_mode(self, mode: PermissionMode) -> None:
        self._mode = mode

    @property
    def mode(self) -> PermissionMode:
        return self._mode

    def set_callback(self, callback: Callable[[PermissionRequest], bool]) -> None:
        self._callback = callback

    def _matches_pattern(self, tool_name: str, pattern: str) -> bool:
        if "*" in pattern or "?" in pattern:
            return fnmatch.fnmatch(tool_name, pattern)
        return tool_name == pattern

    def _rule_decision(self, tool_name: str) -> PermissionResult | None:
        for rule in self._rules:
            if self._matches_pattern(tool_name, rule.tool_pattern):
                if rule.action == "deny":
                    return PermissionResult.DENIED
                if rule.action == "allow":
                    return PermissionResult.ALLOWED
        return None

    def _allow_patterns(self) -> list[str]:
        return [r.tool_pattern for r in self._rules if r.action == "allow"]

    def _deny_patterns(self) -> list[str]:
        return [r.tool_pattern for r in self._rules if r.action == "deny"]

    def check(
        self,
        tool_name: str,
        input_data: Optional[dict[str, Any]] = None,
        reason: str = "",
    ) -> PermissionResult:
        # Explicit rule match has highest priority.
        rule_decision = self._rule_decision(tool_name)
        if rule_decision is not None:
            return rule_decision

        # Explicit user approval cache next.
        cache_key = f"{tool_name}:{str(input_data)}"
        if cache_key in self._approval_cache:
            return PermissionResult.ALLOWED if self._approval_cache[cache_key] else PermissionResult.DENIED

        # Canonical permission semantics.
        checker = create_permission_checker(
            mode=self._mode,
            always_allow=self._allow_patterns(),
            always_deny=self._deny_patterns(),
        )
        allowed = checker.can_execute(tool_name)
        if allowed:
            return PermissionResult.ALLOWED

        # Compatibility behavior: ask in interactive-ish modes.
        if self._mode in (
            PermissionMode.DEFAULT,
            PermissionMode.AUTO,
            PermissionMode.PLAN,
            PermissionMode.ACCEPT_EDITS,
        ):
            return PermissionResult.ASK

        return PermissionResult.DENIED

    def approve(
        self,
        tool_name: str,
        input_data: Optional[dict[str, Any]] = None,
    ) -> None:
        self._approval_cache[f"{tool_name}:{str(input_data)}"] = True

    def deny(
        self,
        tool_name: str,
        input_data: Optional[dict[str, Any]] = None,
    ) -> None:
        self._approval_cache[f"{tool_name}:{str(input_data)}"] = False

    def clear_cache(self) -> None:
        self._approval_cache.clear()

    def add_rule(
        self,
        tool_pattern: str,
        action: str = "allow",
        conditions: Optional[dict[str, Any]] = None,
    ) -> PermissionRule:
        rule = PermissionRule(
            tool_pattern=tool_pattern,
            action=action,
            conditions=conditions or {},
        )
        self._rules.append(rule)
        return rule

    def remove_rule(self, tool_pattern: str) -> bool:
        for i, rule in enumerate(self._rules):
            if rule.tool_pattern == tool_pattern:
                self._rules.pop(i)
                return True
        return False

    def format_status(self) -> str:
        lines: list[str] = [
            "Permission Mode",
            "=" * 40,
            f"Mode: {self._mode.value}",
            f"Rules: {len(self._rules)}",
            f"Cached approvals: {len(self._approval_cache)}",
        ]
        return "\n".join(lines)


_permissions_manager: Optional[PermissionsManager] = None


def get_permissions_manager() -> PermissionsManager:
    """Get or create the global permissions manager."""
    global _permissions_manager
    if _permissions_manager is None:
        mode = (
            os.getenv("CLAUDE_PERMISSION_MODE")
            or os.getenv("CLAUDE_PERMISSIONS")
            or "default"
        )
        try:
            perm_mode = PermissionMode(mode.lower())
        except ValueError:
            perm_mode = PermissionMode.DEFAULT

        _permissions_manager = PermissionsManager(mode=perm_mode)

    return _permissions_manager


__all__ = [
    "PermissionsManager",
    "PermissionMode",
    "PermissionResult",
    "PermissionRule",
    "PermissionRequest",
    "get_permissions_manager",
]

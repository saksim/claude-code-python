"""Compatibility permission layer for engine-facing workflows.

This module now delegates decision semantics to the canonical permission
implementation in ``claude_code.permissions`` while preserving the historical
API surface used by older call sites.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from claude_code.permissions import PermissionMode, create_permission_checker


class PermissionBehavior(Enum):
    """What to do when permission is requested."""

    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


@dataclass(frozen=True, slots=True)
class PermissionDecision:
    """Result of a permission check."""

    behavior: PermissionBehavior
    message: str | None = None
    updated_input: dict[str, Any] | None = None
    suggestions: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class PermissionRule:
    """A permission rule pattern."""

    tool_pattern: str
    input_pattern: str | None = None
    behavior: PermissionBehavior = PermissionBehavior.ALLOW
    description: str | None = None


@dataclass
class PermissionContext:
    """Context for permission decisions."""

    mode: PermissionMode
    always_allow_rules: list[PermissionRule] = field(default_factory=list)
    always_deny_rules: list[PermissionRule] = field(default_factory=list)
    always_ask_rules: list[PermissionRule] = field(default_factory=list)
    additional_working_directories: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.always_allow_rules = [
            PermissionRule(
                tool_pattern=rule.tool_pattern,
                input_pattern=rule.input_pattern,
                behavior=PermissionBehavior.ALLOW,
                description=rule.description,
            )
            for rule in self.always_allow_rules
        ]
        self.always_deny_rules = [
            PermissionRule(
                tool_pattern=rule.tool_pattern,
                input_pattern=rule.input_pattern,
                behavior=PermissionBehavior.DENY,
                description=rule.description,
            )
            for rule in self.always_deny_rules
        ]
        self.always_ask_rules = [
            PermissionRule(
                tool_pattern=rule.tool_pattern,
                input_pattern=rule.input_pattern,
                behavior=PermissionBehavior.ASK,
                description=rule.description,
            )
            for rule in self.always_ask_rules
        ]


@dataclass(frozen=True, slots=True)
class ToolCall:
    """Represents a tool call for permission checking."""

    tool_name: str
    input_data: dict[str, Any]
    source: str = "api"
    agent_id: str | None = None


class PermissionChecker:
    """Compatibility checker that delegates to canonical permissions."""

    def __init__(self, context: PermissionContext | None = None) -> None:
        self.context = context or PermissionContext(mode=PermissionMode.DEFAULT)
        self._denied_count: int = 0
        self._allowed_count: int = 0

    @property
    def denied_count(self) -> int:
        return self._denied_count

    @property
    def allowed_count(self) -> int:
        return self._allowed_count

    def _match_pattern(self, text: str, pattern: str) -> bool:
        if pattern == "*":
            return True
        regex = pattern.replace(".", "\\.").replace("*", ".*").replace("?", ".")
        return bool(re.match(f"^{regex}$", text))

    def _matches_rule(self, tool_call: ToolCall, rule: PermissionRule) -> bool:
        if not self._match_pattern(tool_call.tool_name, rule.tool_pattern):
            return False
        if rule.input_pattern:
            input_str = str(tool_call.input_data)
            if not re.search(rule.input_pattern, input_str):
                return False
        return True

    def _always_allow_patterns(self) -> list[str]:
        return [r.tool_pattern for r in self.context.always_allow_rules]

    def _always_deny_patterns(self) -> list[str]:
        return [r.tool_pattern for r in self.context.always_deny_rules]

    def _get_suggestions(self, tool_call: ToolCall) -> list[dict[str, Any]]:
        return [
            {
                "type": "addRule",
                "rule": tool_call.tool_name,
                "behavior": "allow",
                "destination": "localSettings",
            }
        ]

    def check(self, tool_call: ToolCall) -> PermissionDecision:
        for rule in self.context.always_deny_rules:
            if self._matches_rule(tool_call, rule):
                self._denied_count += 1
                return PermissionDecision(
                    behavior=PermissionBehavior.DENY,
                    message=f"Tool '{tool_call.tool_name}' is denied by rule: {rule.description or rule.tool_pattern}",
                )

        for rule in self.context.always_allow_rules:
            if self._matches_rule(tool_call, rule):
                self._allowed_count += 1
                return PermissionDecision(
                    behavior=PermissionBehavior.ALLOW,
                    updated_input=tool_call.input_data,
                )

        for rule in self.context.always_ask_rules:
            if self._matches_rule(tool_call, rule):
                return PermissionDecision(
                    behavior=PermissionBehavior.ASK,
                    message=f"Tool '{tool_call.tool_name}' requires permission",
                    suggestions=self._get_suggestions(tool_call),
                )

        if self.context.mode in (PermissionMode.BYPASS, PermissionMode.YOLO):
            self._allowed_count += 1
            return PermissionDecision(behavior=PermissionBehavior.ALLOW)

        canonical = create_permission_checker(
            mode=self.context.mode,
            always_allow=self._always_allow_patterns(),
            always_deny=self._always_deny_patterns(),
        )
        if canonical.can_execute(tool_call.tool_name):
            self._allowed_count += 1
            return PermissionDecision(
                behavior=PermissionBehavior.ALLOW,
                updated_input=tool_call.input_data,
            )

        # Historical behavior asked for confirmation for restrictive modes.
        if self.context.mode in (
            PermissionMode.DEFAULT,
            PermissionMode.AUTO,
            PermissionMode.PLAN,
            PermissionMode.ACCEPT_EDITS,
        ):
            return PermissionDecision(
                behavior=PermissionBehavior.ASK,
                message=f"Tool '{tool_call.tool_name}' requires permission",
                suggestions=self._get_suggestions(tool_call),
            )

        self._denied_count += 1
        return PermissionDecision(
            behavior=PermissionBehavior.DENY,
            message=f"Tool '{tool_call.tool_name}' is denied",
        )

    async def check_async(self, tool_call: ToolCall) -> PermissionDecision:
        return self.check(tool_call)

    def update_rules_from_config(self, rules: list[str]) -> None:
        self.context.always_allow_rules = []
        self.context.always_deny_rules = []
        for rule_str in rules:
            parts = rule_str.strip().split(maxsplit=1)
            tool_pattern = parts[0]
            input_pattern = parts[1] if len(parts) > 1 else None
            if tool_pattern.startswith("!"):
                self.context.always_deny_rules.append(
                    PermissionRule(tool_pattern=tool_pattern[1:], input_pattern=input_pattern, behavior=PermissionBehavior.DENY)
                )
            else:
                self.context.always_allow_rules.append(
                    PermissionRule(tool_pattern=tool_pattern, input_pattern=input_pattern, behavior=PermissionBehavior.ALLOW)
                )

    def add_rule(self, rule: PermissionRule) -> None:
        if rule.behavior == PermissionBehavior.ALLOW:
            self.context.always_allow_rules.append(rule)
        elif rule.behavior == PermissionBehavior.DENY:
            self.context.always_deny_rules.append(rule)
        else:
            self.context.always_ask_rules.append(rule)

    def remove_rule(self, tool_pattern: str) -> None:
        self.context.always_allow_rules = [r for r in self.context.always_allow_rules if r.tool_pattern != tool_pattern]
        self.context.always_deny_rules = [r for r in self.context.always_deny_rules if r.tool_pattern != tool_pattern]
        self.context.always_ask_rules = [r for r in self.context.always_ask_rules if r.tool_pattern != tool_pattern]

    def get_rules(self) -> dict[str, list[str]]:
        rules: dict[str, list[str]] = {
            "always_allow": [],
            "always_deny": [],
            "always_ask": [],
        }
        for rule in self.context.always_allow_rules:
            rules["always_allow"].append(
                f"{rule.tool_pattern} {rule.input_pattern}" if rule.input_pattern else rule.tool_pattern
            )
        for rule in self.context.always_deny_rules:
            body = f"{rule.tool_pattern} {rule.input_pattern}" if rule.input_pattern else rule.tool_pattern
            rules["always_deny"].append(f"!{body}")
        for rule in self.context.always_ask_rules:
            rules["always_ask"].append(
                f"{rule.tool_pattern} {rule.input_pattern}" if rule.input_pattern else rule.tool_pattern
            )
        return rules


class InteractivePermissionAsker:
    """Interactive asker for compatibility paths."""

    def __init__(self, console: Any | None = None) -> None:
        self._console = console
        self._auto_approved_count: int = 0
        self._user_approved_count: int = 0
        self._user_denied_count: int = 0

    async def ask(
        self,
        tool_call: ToolCall,
        message: str,
        suggestions: list[dict[str, Any]],
    ) -> PermissionDecision:
        if not self._console:
            self._user_denied_count += 1
            return PermissionDecision(
                behavior=PermissionBehavior.DENY,
                message="Permission denied (non-interactive mode)",
            )

        from rich.console import Console
        from rich.panel import Panel
        from rich.prompt import Confirm

        console = Console()
        lines = [f"**Tool:** {tool_call.tool_name}"]
        if tool_call.input_data:
            lines.append("**Input:**")
            for key, value in list(tool_call.input_data.items())[:5]:
                lines.append(f"  - {key}: {str(value)[:100]}")

        console.print(Panel("\n".join(lines), title="Permission Required", border_style="yellow"))
        console.print(f"\n{message}")

        try:
            response = Confirm.ask("Allow this tool?", default=False)
        except (EOFError, KeyboardInterrupt):
            response = False

        if response:
            self._user_approved_count += 1
            return PermissionDecision(behavior=PermissionBehavior.ALLOW, updated_input=tool_call.input_data)

        self._user_denied_count += 1
        return PermissionDecision(behavior=PermissionBehavior.DENY, message="Permission denied by user")

    def get_stats(self) -> dict[str, Any]:
        return {
            "auto_approved": self._auto_approved_count,
            "user_approved": self._user_approved_count,
            "user_denied": self._user_denied_count,
        }


class PermissionManager:
    """Compatibility manager composed of checker and asker."""

    def __init__(
        self,
        checker: PermissionChecker | None = None,
        asker: InteractivePermissionAsker | None = None,
    ) -> None:
        self._checker = checker or PermissionChecker()
        self._asker = asker or InteractivePermissionAsker()

    @property
    def checker(self) -> PermissionChecker:
        return self._checker

    @property
    def asker(self) -> InteractivePermissionAsker:
        return self._asker

    def set_mode(self, mode: PermissionMode) -> None:
        self._checker.context.mode = mode

    def get_mode(self) -> PermissionMode:
        return self._checker.context.mode

    async def check_tool(
        self,
        tool_name: str,
        input_data: dict[str, Any],
        source: str = "api",
    ) -> PermissionDecision:
        tool_call = ToolCall(tool_name=tool_name, input_data=input_data, source=source)
        decision = await self._checker.check_async(tool_call)
        if decision.behavior == PermissionBehavior.ASK:
            decision = await self._asker.ask(
                tool_call,
                decision.message or "Allow this tool?",
                decision.suggestions,
            )
        return decision

    def add_allow_rule(self, pattern: str, input_pattern: str | None = None) -> None:
        self._checker.add_rule(
            PermissionRule(tool_pattern=pattern, input_pattern=input_pattern, behavior=PermissionBehavior.ALLOW)
        )

    def add_deny_rule(self, pattern: str, input_pattern: str | None = None) -> None:
        self._checker.add_rule(
            PermissionRule(tool_pattern=pattern, input_pattern=input_pattern, behavior=PermissionBehavior.DENY)
        )

    def remove_rule(self, pattern: str) -> None:
        self._checker.remove_rule(pattern)

    def get_rules(self) -> dict[str, list[str]]:
        return self._checker.get_rules()

    def export_rules(self) -> str:
        return json.dumps(self.get_rules(), indent=2)

    def import_rules(self, rules: list[str]) -> None:
        self._checker.update_rules_from_config(rules)

    def get_stats(self) -> dict[str, Any]:
        return {
            "checker": {
                "denied": self._checker.denied_count,
                "allowed": self._checker.allowed_count,
            },
            "asker": self._asker.get_stats(),
            "mode": self._checker.context.mode.value,
        }


__all__ = [
    "PermissionBehavior",
    "PermissionDecision",
    "PermissionRule",
    "PermissionContext",
    "ToolCall",
    "PermissionChecker",
    "InteractivePermissionAsker",
    "PermissionManager",
]

"""Permission System for Claude Code Python.

Handles tool execution permissions with rule-based access control.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PermissionBehavior(Enum):
    """What to do when permission is requested."""

    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


@dataclass(frozen=True, slots=True)
class PermissionDecision:
    """Result of a permission check.

    Attributes:
        behavior: The permission behavior decision.
        message: Optional message explaining the decision.
        updated_input: Optional modified input data.
        suggestions: List of suggestions for allowing the tool.
    """

    behavior: PermissionBehavior
    message: str | None = None
    updated_input: dict[str, Any] | None = None
    suggestions: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class PermissionRule:
    """A permission rule pattern.

    Attributes:
        tool_pattern: Pattern to match tool names.
        input_pattern: Optional pattern to match input data.
        behavior: The behavior for matching calls.
        description: Optional description of the rule.
    """

    tool_pattern: str
    input_pattern: str | None = None
    behavior: PermissionBehavior = PermissionBehavior.ALLOW
    description: str | None = None


class PermissionMode(Enum):
    """Permission mode setting."""

    DEFAULT = "default"  # Ask for permission
    AUTO = "auto"  # Auto-approve based on rules
    PLAN = "plan"  # Ask for everything
    BYPASS = "bypass"  # No permission checks
    YOLO = "yolo"  # Auto-approve everything


@dataclass
class PermissionContext:
    """Context for permission decisions.

    Attributes:
        mode: Current permission mode.
        always_allow_rules: Rules for automatically allowing tools.
        always_deny_rules: Rules for automatically denying tools.
        always_ask_rules: Rules for always asking user.
        additional_working_directories: Additional working directories.
    """

    mode: PermissionMode
    always_allow_rules: list[PermissionRule] = field(default_factory=list)
    always_deny_rules: list[PermissionRule] = field(default_factory=list)
    always_ask_rules: list[PermissionRule] = field(default_factory=list)
    additional_working_directories: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Post-initialization processing."""
        for rule in self.always_allow_rules:
            rule.behavior = PermissionBehavior.ALLOW
        for rule in self.always_deny_rules:
            rule.behavior = PermissionBehavior.DENY
        for rule in self.always_ask_rules:
            rule.behavior = PermissionBehavior.ASK


@dataclass(frozen=True, slots=True)
class ToolCall:
    """Represents a tool call for permission checking.

    Attributes:
        tool_name: Name of the tool being called.
        input_data: Input data for the tool.
        source: Source of the call (api, hook, command).
        agent_id: Optional ID of the agent making the call.
    """

    tool_name: str
    input_data: dict[str, Any]
    source: str = "api"
    agent_id: str | None = None


class PermissionChecker:
    """Checks permissions for tool execution.

    Implements rule-based permission checking with pattern matching.
    """

    def __init__(self, context: PermissionContext | None = None) -> None:
        """Initialize PermissionChecker.

        Args:
            context: Permission context (uses default if not provided).
        """
        self.context = context or PermissionContext(mode=PermissionMode.DEFAULT)
        self._denied_count: int = 0
        self._allowed_count: int = 0

    @property
    def denied_count(self) -> int:
        """Number of denied tool calls."""
        return self._denied_count

    @property
    def allowed_count(self) -> int:
        """Number of allowed tool calls."""
        return self._allowed_count

    def check(self, tool_call: ToolCall) -> PermissionDecision:
        """Check if a tool call should be allowed.

        Args:
            tool_call: The tool call to check.

        Returns:
            PermissionDecision with the result.
        """
        if self.context.mode == PermissionMode.BYPASS:
            self._allowed_count += 1
            return PermissionDecision(behavior=PermissionBehavior.ALLOW)

        if self.context.mode == PermissionMode.YOLO:
            self._allowed_count += 1
            return PermissionDecision(behavior=PermissionBehavior.ALLOW)

        if self.context.mode == PermissionMode.PLAN:
            return PermissionDecision(
                behavior=PermissionBehavior.ASK,
                message=f"Tool '{tool_call.tool_name}' requires permission",
                suggestions=self._get_suggestions(tool_call),
            )

        if self.context.mode == PermissionMode.AUTO:
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

        return PermissionDecision(
            behavior=PermissionBehavior.ASK,
            message=f"Tool '{tool_call.tool_name}' requires permission",
            suggestions=self._get_suggestions(tool_call),
        )

    def _matches_rule(self, tool_call: ToolCall, rule: PermissionRule) -> bool:
        """Check if a tool call matches a rule.

        Args:
            tool_call: The tool call to check.
            rule: The permission rule to match against.

        Returns:
            True if the tool call matches the rule.
        """
        if not self._match_pattern(tool_call.tool_name, rule.tool_pattern):
            return False

        if rule.input_pattern:
            input_str = str(tool_call.input_data)
            if not re.search(rule.input_pattern, input_str):
                return False

        return True

    def _match_pattern(self, text: str, pattern: str) -> bool:
        """Match text against a pattern with wildcards.

        Args:
            text: Text to match.
            pattern: Pattern with optional wildcards (* and ?).

        Returns:
            True if the text matches the pattern.
        """
        if pattern == "*":
            return True

        regex = pattern.replace(".", "\\.").replace("*", ".*").replace("?", ".")
        return bool(re.match(f"^{regex}$", text))

    def _get_suggestions(self, tool_call: ToolCall) -> list[dict[str, Any]]:
        """Get suggestions for allowing the tool.

        Args:
            tool_call: The tool call to get suggestions for.

        Returns:
            List of suggestion dictionaries.
        """
        return [
            {
                "type": "addRule",
                "rule": tool_call.tool_name,
                "behavior": "allow",
                "destination": "localSettings",
            }
        ]

    async def check_async(self, tool_call: ToolCall) -> PermissionDecision:
        """Async version of check.

        Args:
            tool_call: The tool call to check.

        Returns:
            PermissionDecision with the result.
        """
        return self.check(tool_call)

    def update_rules_from_config(self, rules: list[str]) -> None:
        """Update rules from configuration strings.

        Rules format: "tool_pattern input_pattern?" or just "tool_pattern"
        Prefix with "!" for deny rules.

        Args:
            rules: List of rule strings.
        """
        self.context.always_allow_rules = []
        self.context.always_deny_rules = []

        for rule_str in rules:
            parts = rule_str.strip().split(maxsplit=1)
            tool_pattern = parts[0]
            input_pattern = parts[1] if len(parts) > 1 else None

            rule = PermissionRule(
                tool_pattern=tool_pattern,
                input_pattern=input_pattern,
            )

            if tool_pattern.startswith("!"):
                rule.tool_pattern = tool_pattern[1:]
                self.context.always_deny_rules.append(rule)
            else:
                self.context.always_allow_rules.append(rule)

    def add_rule(self, rule: PermissionRule) -> None:
        """Add a permission rule.

        Args:
            rule: The rule to add.
        """
        if rule.behavior == PermissionBehavior.ALLOW:
            self.context.always_allow_rules.append(rule)
        elif rule.behavior == PermissionBehavior.DENY:
            self.context.always_deny_rules.append(rule)
        else:
            self.context.always_ask_rules.append(rule)

    def remove_rule(self, tool_pattern: str) -> None:
        """Remove a rule by tool pattern.

        Args:
            tool_pattern: Pattern of the rule to remove.
        """
        self.context.always_allow_rules = [
            r for r in self.context.always_allow_rules
            if r.tool_pattern != tool_pattern
        ]
        self.context.always_deny_rules = [
            r for r in self.context.always_deny_rules
            if r.tool_pattern != tool_pattern
        ]
        self.context.always_ask_rules = [
            r for r in self.context.always_ask_rules
            if r.tool_pattern != tool_pattern
        ]

    def get_rules(self) -> dict[str, list[str]]:
        """Get all rules as strings.

        Returns:
            Dictionary with rule lists by category.
        """
        rules: dict[str, list[str]] = {
            "always_allow": [],
            "always_deny": [],
            "always_ask": [],
        }

        for rule in self.context.always_allow_rules:
            if rule.input_pattern:
                rules["always_allow"].append(f"{rule.tool_pattern} {rule.input_pattern}")
            else:
                rules["always_allow"].append(rule.tool_pattern)

        for rule in self.context.always_deny_rules:
            prefix = "!" if rule.behavior == PermissionBehavior.DENY else ""
            if rule.input_pattern:
                rules["always_deny"].append(f"{prefix}{rule.tool_pattern} {rule.input_pattern}")
            else:
                rules["always_deny"].append(f"{prefix}{rule.tool_pattern}")

        for rule in self.context.always_ask_rules:
            if rule.input_pattern:
                rules["always_ask"].append(f"{rule.tool_pattern} {rule.input_pattern}")
            else:
                rules["always_ask"].append(rule.tool_pattern)

        return rules


class InteractivePermissionAsker:
    """Asks user for permission interactively.

    Used when permission cannot be auto-approved.
    """

    def __init__(self, console: Any | None = None) -> None:
        """Initialize InteractivePermissionAsker.

        Args:
            console: Optional console for interactive prompts.
        """
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
        """Ask the user for permission.

        Args:
            tool_call: The tool call requiring permission.
            message: Message to show the user.
            suggestions: Suggestions for allowing.

        Returns:
            User's decision.
        """
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

        panel = Panel(
            "\n".join(lines),
            title="Permission Required",
            border_style="yellow",
        )
        console.print(panel)
        console.print(f"\n{message}")

        try:
            response = Confirm.ask("Allow this tool?", default=False)
        except (EOFError, KeyboardInterrupt):
            response = False

        if response:
            self._user_approved_count += 1
            return PermissionDecision(
                behavior=PermissionBehavior.ALLOW,
                updated_input=tool_call.input_data,
            )
        else:
            self._user_denied_count += 1
            return PermissionDecision(
                behavior=PermissionBehavior.DENY,
                message="Permission denied by user",
            )

    def get_stats(self) -> dict[str, Any]:
        """Get permission statistics.

        Returns:
            Dictionary with permission statistics.
        """
        return {
            "auto_approved": self._auto_approved_count,
            "user_approved": self._user_approved_count,
            "user_denied": self._user_denied_count,
        }


class PermissionManager:
    """Manages permissions across the application.

    Coordinates between permission checker and interactive asker.
    """

    def __init__(
        self,
        checker: PermissionChecker | None = None,
        asker: InteractivePermissionAsker | None = None,
    ) -> None:
        """Initialize PermissionManager.

        Args:
            checker: Permission checker instance.
            asker: Interactive permission asker instance.
        """
        self._checker = checker or PermissionChecker()
        self._asker = asker or InteractivePermissionAsker()

    @property
    def checker(self) -> PermissionChecker:
        """Get the permission checker."""
        return self._checker

    @property
    def asker(self) -> InteractivePermissionAsker:
        """Get the permission asker."""
        return self._asker

    def set_mode(self, mode: PermissionMode) -> None:
        """Set the permission mode.

        Args:
            mode: The new permission mode.
        """
        self._checker.context.mode = mode

    def get_mode(self) -> PermissionMode:
        """Get the current permission mode.

        Returns:
            Current permission mode.
        """
        return self._checker.context.mode

    async def check_tool(
        self,
        tool_name: str,
        input_data: dict[str, Any],
        source: str = "api",
    ) -> PermissionDecision:
        """Check if a tool should be allowed to run.

        Args:
            tool_name: Name of the tool.
            input_data: Tool input parameters.
            source: Source of the call.

        Returns:
            Permission decision.
        """
        tool_call = ToolCall(
            tool_name=tool_name,
            input_data=input_data,
            source=source,
        )

        decision = await self._checker.check_async(tool_call)

        if decision.behavior == PermissionBehavior.ASK:
            decision = await self._asker.ask(
                tool_call,
                decision.message or "Allow this tool?",
                decision.suggestions,
            )

        return decision

    def add_allow_rule(
        self,
        pattern: str,
        input_pattern: str | None = None,
    ) -> None:
        """Add an allow rule.

        Args:
            pattern: Tool pattern to allow.
            input_pattern: Optional input pattern.
        """
        rule = PermissionRule(
            tool_pattern=pattern,
            input_pattern=input_pattern,
            behavior=PermissionBehavior.ALLOW,
        )
        self._checker.add_rule(rule)

    def add_deny_rule(
        self,
        pattern: str,
        input_pattern: str | None = None,
    ) -> None:
        """Add a deny rule.

        Args:
            pattern: Tool pattern to deny.
            input_pattern: Optional input pattern.
        """
        rule = PermissionRule(
            tool_pattern=pattern,
            input_pattern=input_pattern,
            behavior=PermissionBehavior.DENY,
        )
        self._checker.add_rule(rule)

    def remove_rule(self, pattern: str) -> None:
        """Remove a rule by pattern.

        Args:
            pattern: Pattern of the rule to remove.
        """
        self._checker.remove_rule(pattern)

    def get_rules(self) -> dict[str, list[str]]:
        """Get all rules.

        Returns:
            Dictionary with rule lists by category.
        """
        return self._checker.get_rules()

    def export_rules(self) -> str:
        """Export rules as JSON-serializable string.

        Returns:
            JSON string of rules.
        """
        return json.dumps(self.get_rules(), indent=2)

    def import_rules(self, rules: list[str]) -> None:
        """Import rules from list of strings.

        Args:
            rules: List of rule strings.
        """
        self._checker.update_rules_from_config(rules)

    def get_stats(self) -> dict[str, Any]:
        """Get permission statistics.

        Returns:
            Dictionary with permission statistics.
        """
        return {
            "checker": {
                "denied": self._checker.denied_count,
                "allowed": self._checker.allowed_count,
            },
            "asker": self._asker.get_stats(),
            "mode": self._checker.context.mode.value,
        }
"""
Claude Code Python - Command Graph

Provides command classification and organization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from claude_code.porting.snapshots import (
    PORTED_COMMANDS,
    get_all_command_names,
    find_commands,
)


@dataclass(frozen=True, slots=True)
class CommandGraph:
    """Command graph showing command categories.
    
    Attributes:
        builtins: Built-in commands
        plugin_like: Plugin commands
        skill_like: Skill commands
    """
    builtins: tuple[str, ...] = field(default_factory=tuple)
    plugin_like: tuple[str, ...] = field(default_factory=tuple)
    skill_like: tuple[str, ...] = field(default_factory=tuple)

    def flattened(self) -> tuple[str, ...]:
        """Get all commands as a flat tuple."""
        return self.builtins + self.plugin_like + self.skill_like

    def as_markdown(self) -> str:
        """Convert to markdown format."""
        lines = [
            "# Command Graph",
            "",
            f"Builtins: {len(self.builtins)}",
            f"Plugin-like commands: {len(self.plugin_like)}",
            f"Skill-like commands: {len(self.skill_like)}",
            "",
            "## Builtins",
        ]
        
        builtin_lines = [f"- {cmd}" for cmd in self.builtins[:20]] if self.builtins else ["- none"]
        lines.extend(builtin_lines)
        
        if self.plugin_like:
            lines.extend(["", "## Plugin-like"])
            lines.extend(f"- {cmd}" for cmd in self.plugin_like[:20])
        
        if self.skill_like:
            lines.extend(["", "## Skill-like"])
            lines.extend(f"- {cmd}" for cmd in self.skill_like[:20])
        
        return "\n".join(lines)

    def get_total_count(self) -> int:
        """Get total command count."""
        return len(self.flattened())

    def get_category(self, command: str) -> Optional[str]:
        """Get the category of a command.
        
        Args:
            command: Command name
            
        Returns:
            Category name or None if not found
        """
        if command in self.builtins:
            return "builtin"
        if command in self.plugin_like:
            return "plugin"
        if command in self.skill_like:
            return "skill"
        return None


def build_command_graph() -> CommandGraph:
    """Build the command graph from snapshots.
    
    Returns:
        CommandGraph instance
    """
    commands = list(PORTED_COMMANDS)
    
    builtins = tuple(
        module.name for module in commands
        if "plugin" not in module.source_hint.lower() 
        and "skills" not in module.source_hint.lower()
    )
    
    plugin_like = tuple(
        module.name for module in commands
        if "plugin" in module.source_hint.lower()
    )
    
    skill_like = tuple(
        module.name for module in commands
        if "skills" in module.source_hint.lower()
    )
    
    return CommandGraph(
        builtins=builtins,
        plugin_like=plugin_like,
        skill_like=skill_like,
    )


def get_command_categories() -> dict[str, list[str]]:
    """Get commands grouped by category.
    
    Returns:
        Dictionary mapping category to command list
    """
    graph = build_command_graph()
    return {
        "builtin": list(graph.builtins),
        "plugin": list(graph.plugin_like),
        "skill": list(graph.skill_like),
    }


__all__ = [
    "CommandGraph",
    "build_command_graph",
    "get_command_categories",
]
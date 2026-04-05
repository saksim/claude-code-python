"""
Claude Code Python - Execution Registry

Provides command and tool execution registry for mirrored operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Callable

from claude_code.porting.snapshots import (
    PORTED_COMMANDS,
    PORTED_TOOLS,
    get_command_snapshot,
    get_tool_snapshot,
)


@dataclass(frozen=True)
class MirroredCommand:
    """A mirrored command from the porting workspace.
    
    Attributes:
        name: Command name
        source_hint: Original source path
        executor: Optional executor function
    """
    name: str
    source_hint: str
    executor: Optional[Callable[[str], str]] = None

    def execute(self, prompt: str = "") -> str:
        """Execute the command.
        
        Args:
            prompt: Command prompt/arguments
            
        Returns:
            Execution result message
        """
        if self.executor:
            return self.executor(prompt)
        return f"Mirrored command '{self.name}' from {self.source_hint} would handle prompt {prompt!r}."


@dataclass(frozen=True)
class MirroredTool:
    """A mirrored tool from the porting workspace.
    
    Attributes:
        name: Tool name
        source_hint: Original source path
        executor: Optional executor function
    """
    name: str
    source_hint: str
    executor: Optional[Callable[[str], str]] = None

    def execute(self, payload: str = "") -> str:
        """Execute the tool.
        
        Args:
            payload: Tool payload
            
        Returns:
            Execution result message
        """
        if self.executor:
            return self.executor(payload)
        return f"Mirrored tool '{self.name}' from {self.source_hint} would handle payload {payload!r}."


@dataclass
class ExecutionRegistry:
    """Registry for executing mirrored commands and tools.
    
    Attributes:
        commands: Tuple of mirrored commands
        tools: Tuple of mirrored tools
    """
    commands: tuple[MirroredCommand, ...] = ()
    tools: tuple[MirroredTool, ...] = ()

    def command(self, name: str) -> Optional[MirroredCommand]:
        """Get a command by name.
        
        Args:
            name: Command name
            
        Returns:
            MirroredCommand or None if not found
        """
        lowered = name.lower()
        for command in self.commands:
            if command.name.lower() == lowered:
                return command
        return None

    def tool(self, name: str) -> Optional[MirroredTool]:
        """Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            MirroredTool or None if not found
        """
        lowered = name.lower()
        for tool in self.tools:
            if tool.name.lower() == lowered:
                return tool
        return None

    def list_commands(self) -> list[str]:
        """List all command names.
        
        Returns:
            List of command names
        """
        return [cmd.name for cmd in self.commands]

    def list_tools(self) -> list[str]:
        """List all tool names.
        
        Returns:
            List of tool names
        """
        return [tool.name for tool in self.tools]

    def get_total_count(self) -> int:
        """Get total count of commands and tools.
        
        Returns:
            Total count
        """
        return len(self.commands) + len(self.tools)

    def as_markdown(self) -> str:
        """Convert to markdown format.
        
        Returns:
            Markdown formatted string
        """
        lines = [
            "# Execution Registry",
            "",
            f"Commands: {len(self.commands)}",
            f"Tools: {len(self.tools)}",
            "",
            "## Commands",
        ]
        lines.extend(f"- {cmd.name}" for cmd in self.commands[:15])
        
        if len(self.commands) > 15:
            lines.append(f"- ... and {len(self.commands) - 15} more")
        
        lines.extend(["", "## Tools"])
        lines.extend(f"- {tool.name}" for tool in self.tools[:15])
        
        if len(self.tools) > 15:
            lines.append(f"- ... and {len(self.tools) - 15} more")
        
        return "\n".join(lines)


def build_execution_registry() -> ExecutionRegistry:
    """Build the execution registry from snapshots.
    
    Returns:
        ExecutionRegistry instance
    """
    commands = tuple(
        MirroredCommand(module.name, module.source_hint)
        for module in PORTED_COMMANDS
    )
    
    tools = tuple(
        MirroredTool(module.name, module.source_hint)
        for module in PORTED_TOOLS
    )
    
    return ExecutionRegistry(commands=commands, tools=tools)


def register_command_executor(name: str, executor: Callable[[str], str]) -> None:
    """Register an executor for a command.
    
    Args:
        name: Command name
        executor: Executor function
    """
    registry = get_execution_registry()
    for cmd in registry.commands:
        if cmd.name.lower() == name.lower():
            object.__setattr__(cmd, 'executor', executor)


def register_tool_executor(name: str, executor: Callable[[str], str]) -> None:
    """Register an executor for a tool.
    
    Args:
        name: Tool name
        executor: Executor function
    """
    registry = get_execution_registry()
    for tool in registry.tools:
        if tool.name.lower() == name.lower():
            object.__setattr__(tool, 'executor', executor)


# Global registry instance
_registry: Optional[ExecutionRegistry] = None


def get_execution_registry() -> ExecutionRegistry:
    """Get the global execution registry.
    
    Returns:
        ExecutionRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = build_execution_registry()
    return _registry


__all__ = [
    "MirroredCommand",
    "MirroredTool",
    "ExecutionRegistry",
    "build_execution_registry",
    "register_command_executor",
    "register_tool_executor",
    "get_execution_registry",
]
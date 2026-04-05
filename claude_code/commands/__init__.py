"""
Claude Code Python - Slash Commands System
Implements slash commands like /help, /clear, /model, etc.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Command registry pattern
"""

from __future__ import annotations

from typing import Optional
from dataclasses import dataclass, field

from claude_code.commands.base import (
    Command,
    CommandContext,
    CommandResult,
    CommandType,
)
from claude_code.commands.builtins import HelpCommand, ClearCommand


@dataclass(frozen=True, slots=True)
class CommandRegistry:
    """Registry for all available commands.
    
    Manages command registration, retrieval, and aliasing.
    
    Attributes:
        _commands: Dictionary mapping command names to Command instances
    """
    _commands: dict[str, Command] = field(default_factory=dict)
    
    def register(self, command: Command) -> None:
        """Register a command.
        
        Args:
            command: Command instance to register
        """
        self._commands[command.name] = command
        for alias in command.aliases:
            self._commands[alias] = command
    
    def get(self, name: str) -> Optional[Command]:
        """Get a command by name or alias.
        
        Args:
            name: Command name or alias
            
        Returns:
            Command instance or None if not found
        """
        return self._commands.get(name)
    
    def list_all(self) -> list[Command]:
        """List all registered commands.
        
        Returns:
            List of all Command instances
        """
        return list(self._commands.values())


# Global command registry
_command_registry: Optional[CommandRegistry] = None


def get_all_commands() -> dict[str, Command]:
    """Get all available commands.
    
    Returns:
        Dictionary mapping command names to Command instances
    """
    global _command_registry
    
    if _command_registry is None:
        _command_registry = CommandRegistry()
        
        # Register builtin commands
        for cmd_class in [HelpCommand, ClearCommand]:
            cmd = cmd_class()
            _command_registry.register(cmd)
    
    return _command_registry._commands


def register_command(command: Command) -> None:
    """Register a new command globally.
    
    Args:
        command: Command instance to register
    """
    commands = get_all_commands()
    commands[command.name] = command
    for alias in command.aliases:
        commands[alias] = command


__all__ = [
    "Command",
    "CommandContext",
    "CommandResult",
    "CommandType",
    "CommandRegistry",
    "HelpCommand",
    "ClearCommand",
    "get_all_commands",
    "register_command",
]

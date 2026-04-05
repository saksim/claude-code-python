"""
Claude Code Python - REPL Commands
Modular command implementations.
"""

from claude_code.commands.base import Command, SimpleCommand
from claude_code.repl.commands.help import HelpCommand
from claude_code.repl.commands.exit import ExitCommand
from claude_code.repl.commands.clear import ClearCommand
from claude_code.repl.commands.cost import CostCommand

__all__ = [
    "Command",
    "SimpleCommand",
    "HelpCommand",
    "ExitCommand",
    "ClearCommand",
    "CostCommand",
]


def get_all_commands() -> dict[str, Command]:
    """Get all available commands."""
    commands = {}
    
    for cmd_class in [HelpCommand, ExitCommand, ClearCommand, CostCommand]:
        cmd = cmd_class()
        commands.update(cmd.get_commands())
    
    return commands

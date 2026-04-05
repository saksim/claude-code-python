"""Command Registry for Claude Code Python.

Unified command registration and discovery.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from claude_code.commands.base import Command, CommandContext, CommandResult, CommandType


# Store command instances, not classes
COMMANDS: dict[str, "Command"] = {}


def register_command(cmd: "Command") -> None:
    """Register a command instance.

    Args:
        cmd: Command instance to register.
    """
    COMMANDS[cmd.name] = cmd


def get_command(name: str) -> "Command | None":
    """Get a command by name.

    Args:
        name: Command name.

    Returns:
        Command instance or None if not found.
    """
    return COMMANDS.get(name)


def get_all_commands() -> dict[str, Command]:
    """Get all registered commands.

    Returns:
        Dictionary of command name to instance.
    """
    return dict(COMMANDS)


def list_command_names() -> list[str]:
    """List all command names.

    Returns:
        List of command names.
    """
    return list(COMMANDS.keys())


def create_all_commands() -> dict[str, Command]:
    """Get all commands.

    Returns:
        Dictionary of command name to instance.
    """
    return dict(COMMANDS)


def setup_default_commands() -> None:
    """Setup all default commands."""
    from claude_code.commands.mcp import create_mcp_command
    from claude_code.commands.auth import LoginCommand, LogoutCommand, AuthStatusCommand
    from claude_code.commands.config import ConfigCommand
    from claude_code.commands.init import InitCommand, DoctorCommand, VersionCommand
    from claude_code.commands.model import ModelCommand, ThemeCommand
    from claude_code.commands.permissions import PermissionsCommand
    from claude_code.commands.diff import DiffCommand, RenameCommand
    from claude_code.commands.hooks import HooksCommand
    from claude_code.commands.branch import BranchCommand
    from claude_code.commands.compact import CompactCommand, ResumeCommand, RewindCommand
    from claude_code.commands.status import StatusCommand, SessionCommand, MemoryCommand
    from claude_code.commands.skills import SkillsCommand
    from claude_code.commands.tasks import TasksCommand
    from claude_code.commands.review import ReviewCommand

    commands = [
        create_mcp_command,
        LoginCommand,
        LogoutCommand,
        AuthStatusCommand,
        ConfigCommand,
        InitCommand,
        DoctorCommand,
        VersionCommand,
        ModelCommand,
        ThemeCommand,
        PermissionsCommand,
        DiffCommand,
        RenameCommand,
        HooksCommand,
        BranchCommand,
        CompactCommand,
        ResumeCommand,
        RewindCommand,
        StatusCommand,
        SessionCommand,
        MemoryCommand,
        SkillsCommand,
        TasksCommand,
        ReviewCommand,
    ]

    for cmd in commands:
        if callable(cmd):
            cmd = cmd()
        register_command(cmd)


__all__ = [
    "COMMANDS",
    "register_command",
    "get_command",
    "get_all_commands",
    "list_command_names",
    "create_all_commands",
    "setup_default_commands",
]

"""
Claude Code Python - Config Command
Configuration management.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
"""

from __future__ import annotations

import os
from typing import Any

from claude_code.commands.base import Command, CommandContext, CommandResult, CommandType
from claude_code.config import Config, LocalSettings, get_config, save_config


class ConfigGetCommand(Command):
    """Get a configuration value by key."""
    
    def __init__(self) -> None:
        """Initialize the config get command."""
        super().__init__(
            name="get",
            description="Get configuration value",
            command_type=CommandType.LOCAL,
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the config get command.
        
        Args:
            args: Configuration key to retrieve.
            context: The command execution context.
            
        Returns:
            CommandResult with the configuration value.
        """
        config = get_config()
        key = args.strip()
        
        if not key:
            return CommandResult(
                success=False,
                error="Usage: claude config get <key>",
            )
        
        value = getattr(config, key, None)
        
        if value is None:
            return CommandResult(
                success=False,
                error=f"Unknown configuration key: {key}",
            )
        
        return CommandResult(content=f"{key} = {value}")


class ConfigSetCommand(Command):
    """Set a configuration value."""
    
    def __init__(self) -> None:
        """Initialize the config set command."""
        super().__init__(
            name="set",
            description="Set configuration value",
            command_type=CommandType.LOCAL,
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the config set command.
        
        Args:
            args: Configuration key and value (key value).
            context: The command execution context.
            
        Returns:
            CommandResult indicating success or failure.
        """
        config = get_config()
        parts = args.strip().split(maxsplit=1)
        
        if len(parts) < 2:
            return CommandResult(
                success=False,
                error="Usage: claude config set <key> <value>",
            )
        
        key, value = parts
        
        if not hasattr(config, key):
            return CommandResult(
                success=False,
                error=f"Unknown configuration key: {key}",
            )
        
        setattr(config, key, value)
        save_config()
        
        return CommandResult(content=f"Set {key} = {value}")


class ConfigListCommand(Command):
    """List all configuration values."""
    
    def __init__(self) -> None:
        """Initialize the config list command."""
        super().__init__(
            name="list",
            description="List all configuration values",
            command_type=CommandType.LOCAL,
            aliases=["ls"],
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the config list command.
        
        Args:
            args: Command arguments (unused).
            context: The command execution context.
            
        Returns:
            CommandResult with all configuration values.
        """
        config = get_config()
        
        lines: list[str] = ["# Configuration\n"]
        
        for key, value in config.to_dict().items():
            if key == "api_key" and value:
                value = f"sk-ant-{'*' * 20}{value[-4:]}"
            lines.append(f"{key}: {value}")
        
        return CommandResult(content="\n".join(lines))


class ConfigCommand(Command):
    """Manage Claude Code configuration.
    
    Provides subcommands to get, set, and list configuration values.
    Aliases: settings
    """
    
    def __init__(self) -> None:
        """Initialize the config command."""
        super().__init__(
            name="config",
            description="Manage configuration (alias: settings)",
            command_type=CommandType.LOCAL,
            aliases=["settings"],
        )
    
    @property
    def subcommands(self) -> dict[str, Command]:
        """Get subcommand mappings."""
        return {
            "get": ConfigGetCommand(),
            "set": ConfigSetCommand(),
            "list": ConfigListCommand(),
        }
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the config command.
        
        Args:
            args: Command arguments (subcommand and its args).
            context: The command execution context.
            
        Returns:
            CommandResult with subcommand output.
        """
        parts = args.strip().split()
        
        if not parts:
            return await ConfigListCommand().execute("", context)
        
        subcmd = parts[0]
        sub = self.subcommands.get(subcmd)
        
        if sub is None:
            return CommandResult(
                success=False,
                error=f"Unknown subcommand: {subcmd}",
            )
        
        sub_args = " ".join(parts[1:])
        return await sub.execute(sub_args, context)


def create_config_command() -> ConfigCommand:
    """Create the config command."""
    return ConfigCommand()


__all__ = [
    "ConfigCommand",
    "ConfigGetCommand",
    "ConfigSetCommand",
    "ConfigListCommand",
    "create_config_command",
]

"""
Claude Code Python - MCP Command
Manage MCP servers.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- pathlib.Path for file operations
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from claude_code.commands.base import Command, CommandContext, CommandResult, CommandType
from claude_code.services.mcp import get_mcp_manager, MCPConnectionConfig, MCPTransportType


class MCPListCommand(Command):
    """Manage MCP (Model Context Protocol) servers.
    
    Provides subcommands to list, add, remove, and get details
    about configured MCP servers.
    """
    
    def __init__(self) -> None:
        """Initialize the MCP command."""
        super().__init__(
            name="mcp",
            description="Manage MCP servers",
            command_type=CommandType.LOCAL,
        )
    
    @property
    def subcommands(self) -> dict[str, Command]:
        """Get subcommand mappings."""
        return {
            "list": MCPListSubCommand(),
            "add": MCPAddSubCommand(),
            "remove": MCPRemoveSubCommand(),
            "get": MCPGetSubCommand(),
        }
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the MCP command.
        
        Args:
            args: Command arguments (subcommand and its args).
            context: The command execution context.
            
        Returns:
            CommandResult with subcommand output.
        """
        parts = args.strip().split()
        
        if not parts:
            return await self._show_help(context)
        
        subcmd = parts[0]
        sub = self.subcommands.get(subcmd)
        
        if sub is None:
            return CommandResult(
                success=False,
                error=f"Unknown subcommand: {subcmd}",
            )
        
        sub_args = " ".join(parts[1:])
        return await sub.execute(sub_args, context)
    
    async def _show_help(self, context: CommandContext) -> CommandResult:
        """Show help text for MCP command."""
        help_text = """MCP (Model Context Protocol) Server Management

Usage: claude mcp <subcommand> [options]

Subcommands:
  list                  List configured MCP servers
  add <name> <config>  Add an MCP server
  remove <name>        Remove an MCP server
  get <name>           Get details about an MCP server

Examples:
  claude mcp list
  claude mcp add myserver "npx --yes @modelcontextprotocol/server-filesystem /path/to/files"
  claude mcp remove myserver
  claude mcp get myserver
"""
        return CommandResult(content=help_text)


class MCPListSubCommand(Command):
    """List configured MCP servers."""
    
    def __init__(self) -> None:
        """Initialize the MCP list subcommand."""
        super().__init__(
            name="list",
            description="List configured MCP servers",
            command_type=CommandType.LOCAL,
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the MCP list subcommand.
        
        Args:
            args: Command arguments (unused).
            context: The command execution context.
            
        Returns:
            CommandResult with list of MCP servers.
        """
        mcp_manager = get_mcp_manager()
        servers = mcp_manager.list_servers()
        
        if not servers:
            return CommandResult(content="No MCP servers configured")
        
        lines: list[str] = ["# Configured MCP Servers\n"]
        for name, info in servers.items():
            status = "connected" if info["connected"] else "disconnected"
            lines.append(f"\n## {name}")
            lines.append(f"Status: {status}")
            lines.append(f"Tools: {info['tools']}")
            lines.append(f"Resources: {info['resources']}")
        
        return CommandResult(content="\n".join(lines))


class MCPAddSubCommand(Command):
    """Add an MCP server."""
    
    def __init__(self) -> None:
        """Initialize the MCP add subcommand."""
        super().__init__(
            name="add",
            description="Add an MCP server",
            command_type=CommandType.LOCAL,
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the MCP add subcommand.
        
        Args:
            args: Arguments containing server name and command.
            context: The command execution context.
            
        Returns:
            CommandResult indicating success or failure.
        """
        parts = args.strip().split(maxsplit=1)
        
        if len(parts) < 2:
            return CommandResult(
                success=False,
                error="Usage: claude mcp add <name> <command>",
            )
        
        name = parts[0]
        command = parts[1]
        
        config = MCPConnectionConfig(
            server_name=name,
            command=command,
            transport=MCPTransportType.STDIO,
        )
        
        mcp_manager = get_mcp_manager()
        
        try:
            await mcp_manager.add_server(config)
            
            await self._save_to_config(name, config)
            
            return CommandResult(content=f"Added MCP server: {name}")
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to add MCP server: {str(e)}",
            )
    
    async def _save_to_config(self, name: str, config: MCPConnectionConfig) -> None:
        """Save MCP server configuration to .mcp.json."""
        config_path = Path(".mcp.json")
        
        existing: dict[str, Any] = {}
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                existing = json.load(f)
        
        existing[name] = {
            "command": config.command,
            "args": config.args,
            "env": config.env,
        }
        
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)


class MCPRemoveSubCommand(Command):
    """Remove an MCP server."""
    
    def __init__(self) -> None:
        """Initialize the MCP remove subcommand."""
        super().__init__(
            name="remove",
            description="Remove an MCP server",
            command_type=CommandType.LOCAL,
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the MCP remove subcommand.
        
        Args:
            args: Arguments containing the server name to remove.
            context: The command execution context.
            
        Returns:
            CommandResult indicating success or failure.
        """
        name = args.strip()
        
        if not name:
            return CommandResult(
                success=False,
                error="Usage: claude mcp remove <name>",
            )
        
        mcp_manager = get_mcp_manager()
        
        try:
            await mcp_manager.remove_server(name)
            
            await self._remove_from_config(name)
            
            return CommandResult(content=f"Removed MCP server: {name}")
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to remove MCP server: {str(e)}",
            )
    
    async def _remove_from_config(self, name: str) -> None:
        """Remove MCP server from .mcp.json configuration."""
        config_path = Path(".mcp.json")
        
        if not config_path.exists():
            return
        
        with open(config_path, encoding="utf-8") as f:
            existing: dict[str, Any] = json.load(f)
        
        if name in existing:
            del existing[name]
            
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2)


class MCPGetSubCommand(Command):
    """Get details about an MCP server."""
    
    def __init__(self) -> None:
        """Initialize the MCP get subcommand."""
        super().__init__(
            name="get",
            description="Get MCP server details",
            command_type=CommandType.LOCAL,
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the MCP get subcommand.
        
        Args:
            args: Arguments containing the server name.
            context: The command execution context.
            
        Returns:
            CommandResult with server details.
        """
        name = args.strip()
        
        if not name:
            return CommandResult(
                success=False,
                error="Usage: claude mcp get <name>",
            )
        
        mcp_manager = get_mcp_manager()
        client = mcp_manager.get_client(name)
        
        if client is None:
            return CommandResult(
                success=False,
                error=f"MCP server '{name}' not found",
            )
        
        info: dict[str, Any] = {
            "name": client.config.server_name,
            "command": client.config.command,
            "transport": client.config.transport.value,
            "state": client.state.value,
            "tools": len(client.tools),
            "resources": len(client.resources),
        }
        
        lines: list[str] = [f"# MCP Server: {name}\n"]
        for key, value in info.items():
            lines.append(f"{key}: {value}")
        
        if client.tools:
            lines.append("\n## Tools")
            for tool in client.tools:
                lines.append(f"- {tool.name}: {tool.description}")
        
        if client.resources:
            lines.append("\n## Resources")
            for resource in client.resources:
                lines.append(f"- {resource.uri}: {resource.description}")
        
        return CommandResult(content="\n".join(lines))


def create_mcp_command() -> MCPListCommand:
    """Create the MCP command.
    
    Returns:
        A new MCPListCommand instance.
    """
    return MCPListCommand()


__all__ = [
    "MCPListCommand",
    "MCPListSubCommand",
    "MCPAddSubCommand",
    "MCPRemoveSubCommand",
    "MCPGetSubCommand",
    "create_mcp_command",
]

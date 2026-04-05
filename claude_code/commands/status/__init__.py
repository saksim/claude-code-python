"""
Claude Code Python - Status, Session, Memory Commands

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- pathlib.Path for file operations
- Frozen dataclasses where appropriate
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from claude_code.commands.base import Command, CommandContext, CommandResult, CommandType


class StatusCommand(Command):
    """Show current Claude Code status.
    
    Displays session information, API configuration, permission mode,
    and connected MCP servers.
    """
    
    def __init__(self) -> None:
        """Initialize the status command."""
        super().__init__(
            name="status",
            description="Show current status",
            command_type=CommandType.LOCAL,
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the status command.
        
        Args:
            args: Command arguments (unused for status command).
            context: The command execution context.
            
        Returns:
            CommandResult with status information.
        """
        import time
        
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        model = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514")
        
        lines: list[str] = ["# Claude Code Status\n"]
        
        lines.append(f"\n## Session")
        lines.append(f"Working Directory: {context.working_directory}")
        
        if context.session:
            lines.append(f"Session ID: {context.session.get('id', 'N/A')}")
        
        lines.append(f"\n## API")
        lines.append(f"Model: {model}")
        lines.append(f"API Key: {'configured' if api_key else 'not configured'}")
        
        from claude_code.config import get_config
        config = get_config()
        lines.append(f"Permission Mode: {config.permission_mode.value}")
        
        mcp_path = Path(context.working_directory) / ".mcp.json"
        mcp_count = 0
        if mcp_path.exists():
            with open(mcp_path, encoding="utf-8") as f:
                mcp_count = len(json.load(f))
        lines.append(f"MCP Servers: {mcp_count}")
        
        return CommandResult(content="\n".join(lines))


class SessionCommand(Command):
    """Manage Claude Code sessions.
    
    Provides subcommands to list and show information about sessions.
    """
    
    def __init__(self) -> None:
        """Initialize the session command."""
        super().__init__(
            name="session",
            description="Manage sessions",
            command_type=CommandType.LOCAL,
        )
    
    @property
    def subcommands(self) -> dict[str, Command]:
        """Get subcommand mappings."""
        return {
            "list": SessionListCommand(),
            "info": SessionInfoCommand(),
        }
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the session command.
        
        Args:
            args: Command arguments (subcommand and its args).
            context: The command execution context.
            
        Returns:
            CommandResult with subcommand output.
        """
        parts = args.strip().split()
        
        if not parts:
            return await SessionListCommand().execute("", context)
        
        subcmd = parts[0]
        sub = self.subcommands.get(subcmd)
        
        if sub is None:
            return CommandResult(success=False, error=f"Unknown: {subcmd}")
        
        return await sub.execute(" ".join(parts[1:]), context)


class SessionListCommand(Command):
    """List all saved sessions."""
    
    def __init__(self) -> None:
        """Initialize the session list command."""
        super().__init__(name="list", description="List sessions", command_type=CommandType.LOCAL)
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the session list command.
        
        Args:
            args: Command arguments (unused).
            context: The command execution context.
            
        Returns:
            CommandResult with list of sessions.
        """
        sessions_dir = Path.home() / ".claude-code-python" / "sessions"
        
        if not sessions_dir.exists():
            return CommandResult(content="No sessions found")
        
        sessions: list[dict[str, Any]] = []
        for f in sessions_dir.glob("*.json"):
            try:
                with open(f, encoding="utf-8") as fh:
                    data = json.load(fh)
                    sessions.append({"id": f.stem, **data})
            except Exception:
                pass
        
        if not sessions:
            return CommandResult(content="No sessions found")
        
        lines: list[str] = ["# Sessions\n"]
        for s in sorted(sessions, key=lambda x: x.get("last_active", 0), reverse=True)[:10]:
            lines.append(f"\n## {s['id']}")
            lines.append(f"Messages: {s.get('message_count', 0)}")
            lines.append(f"Tools Used: {s.get('tool_call_count', 0)}")
        
        return CommandResult(content="\n".join(lines))


class SessionInfoCommand(Command):
    """Show details of the current session."""
    
    def __init__(self) -> None:
        """Initialize the session info command."""
        super().__init__(name="info", description="Show session info", command_type=CommandType.LOCAL)
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the session info command.
        
        Args:
            args: Command arguments (unused).
            context: The command execution context.
            
        Returns:
            CommandResult with session details.
        """
        if context.session:
            lines: list[str] = ["# Session Info\n"]
            for k, v in context.session.items():
                lines.append(f"{k}: {v}")
            return CommandResult(content="\n".join(lines))
        return CommandResult(content="No active session")


class MemoryCommand(Command):
    """Manage memory files (CLAUDE.md).
    
    Provides subcommands to add, remove, and list CLAUDE.md memory files
    in the current project.
    """
    
    def __init__(self) -> None:
        """Initialize the memory command."""
        super().__init__(
            name="memory",
            description="Manage memory files (CLAUDE.md)",
            command_type=CommandType.LOCAL,
            aliases=["claude"],
        )
    
    @property
    def subcommands(self) -> dict[str, Command]:
        """Get subcommand mappings."""
        return {
            "add": MemoryAddCommand(),
            "remove": MemoryRemoveCommand(),
            "list": MemoryListCommand(),
        }
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the memory command.
        
        Args:
            args: Command arguments (subcommand and its args).
            context: The command execution context.
            
        Returns:
            CommandResult with subcommand output.
        """
        parts = args.strip().split()
        
        if not parts:
            return await MemoryListCommand().execute("", context)
        
        subcmd = parts[0]
        sub = self.subcommands.get(subcmd)
        
        if sub is None:
            return CommandResult(success=False, error=f"Unknown: {subcmd}")
        
        return await sub.execute(" ".join(parts[1:]), context)


class MemoryAddCommand(Command):
    """Add a new CLAUDE.md memory file."""
    
    def __init__(self) -> None:
        """Initialize the memory add command."""
        super().__init__(name="add", description="Add CLAUDE.md file", command_type=CommandType.LOCAL)
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the memory add command.
        
        Args:
            args: Arguments containing filename and content.
            context: The command execution context.
            
        Returns:
            CommandResult indicating success or failure.
        """
        parts = args.strip().split(maxsplit=1)
        name = parts[0] if parts else "CLAUDE.md"
        content = parts[1] if len(parts) > 1 else ""
        
        if not content:
            return CommandResult(success=False, error="Content required")
        
        path = Path(context.working_directory) / name
        path.write_text(content, encoding="utf-8")
        
        return CommandResult(content=f"Created {name}")


class MemoryRemoveCommand(Command):
    """Remove a CLAUDE.md memory file."""
    
    def __init__(self) -> None:
        """Initialize the memory remove command."""
        super().__init__(name="remove", description="Remove CLAUDE.md file", command_type=CommandType.LOCAL)
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the memory remove command.
        
        Args:
            args: Argument containing the filename to remove.
            context: The command execution context.
            
        Returns:
            CommandResult indicating success or failure.
        """
        name = args.strip() or "CLAUDE.md"
        path = Path(context.working_directory) / name
        
        if not path.exists():
            return CommandResult(success=False, error=f"File not found: {name}")
        
        path.unlink()
        return CommandResult(content=f"Removed {name}")


class MemoryListCommand(Command):
    """List all CLAUDE.md memory files."""
    
    def __init__(self) -> None:
        """Initialize the memory list command."""
        super().__init__(name="list", description="List memory files", command_type=CommandType.LOCAL)
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the memory list command.
        
        Args:
            args: Command arguments (unused).
            context: The command execution context.
            
        Returns:
            CommandResult with list of memory files.
        """
        wd = Path(context.working_directory)
        files = list(wd.glob("CLAUDE*.md"))
        
        if not files:
            return CommandResult(content="No CLAUDE.md files found")
        
        lines: list[str] = ["# Memory Files\n"]
        for f in files:
            size = f.stat().st_size
            lines.append(f"- {f.name} ({size} bytes)")
        
        return CommandResult(content="\n".join(lines))


def create_status_command() -> StatusCommand:
    return StatusCommand()

def create_session_command() -> SessionCommand:
    return SessionCommand()

def create_memory_command() -> MemoryCommand:
    return MemoryCommand()


__all__ = [
    "StatusCommand", "SessionCommand", "MemoryCommand",
    "create_status_command", "create_session_command", "create_memory_command",
]

"""
Claude Code Python - Help, Exit, Clear Commands
"""

from __future__ import annotations

from claude_code.commands.base import Command, CommandContext, CommandResult, CommandType


class HelpCommand(Command):
    """Show help."""
    
    def __init__(self):
        super().__init__(
            name="help",
            description="Show help",
            command_type=CommandType.LOCAL,
            aliases=["?"],
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        args = args.strip()
        
        if args:
            return await self._show_command_help(args, context)
        
        return self._show_general_help()
    
    def _show_general_help(self) -> CommandResult:
        return CommandResult(content="""# Claude Code Python

## Commands

### Session
- /status - Show current status
- /session - Manage sessions  
- /resume - Resume previous session
- /compact - Compress conversation

### Configuration
- /config - Manage configuration
- /model - Select model
- /theme - Set theme
- /permissions - Manage permissions

### Tools
- /mcp - Manage MCP servers
- /skills - Manage skills
- /memory - Manage CLAUDE.md files

### Other
- /help - Show this help
- /clear - Clear screen
- /exit - Exit

## Usage

Just type a message to start chatting!
Use /prefix for commands.
""")
    
    async def _show_command_help(self, cmd: str, context: CommandContext) -> CommandResult:
        help_texts = {
            "status": "Show current session status",
            "session": "Manage sessions (list, info)",
            "mcp": "Manage MCP servers (list, add, remove, get)",
            "config": "Manage configuration (get, set, list)",
            "model": "Select model (haiku, sonnet, opus)",
            "compact": "Compress conversation history",
            "resume": "Resume previous session",
            "init": "Initialize project with CLAUDE.md",
        }
        
        if cmd in help_texts:
            return CommandResult(content=f"## {cmd}\n\n{help_texts[cmd]}")
        
        return CommandResult(success=False, error=f"Unknown command: {cmd}")


class ExitCommand(Command):
    """Exit the program."""
    
    def __init__(self):
        super().__init__(
            name="exit",
            description="Exit",
            command_type=CommandType.LOCAL,
            aliases=["quit", "q"],
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        return CommandResult(
            content="Goodbye!",
            is_silent=True,
        )


class ClearCommand(Command):
    """Clear the screen."""
    
    def __init__(self):
        super().__init__(
            name="clear",
            description="Clear screen",
            command_type=CommandType.LOCAL,
            aliases=["cls"],
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        return CommandResult(
            content="\033[2J\033[H",
            is_silent=True,
        )


def create_help_command() -> HelpCommand:
    return HelpCommand()

def create_exit_command() -> ExitCommand:
    return ExitCommand()

def create_clear_command() -> ClearCommand:
    return ClearCommand()


__all__ = [
    "HelpCommand", "ExitCommand", "ClearCommand",
    "create_help_command", "create_exit_command", "create_clear_command",
]

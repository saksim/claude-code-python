"""
Claude Code Python - Help Command
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from claude_code.commands.base import Command, CommandContext, CommandResult, CommandType

if TYPE_CHECKING:
    pass


class HelpCommand(Command):
    """Show help information."""
    
    def __init__(self):
        super().__init__(
            name="help",
            description="Show help information",
            aliases=["h", "?"],
        )
    
    async def execute(
        self,
        args: str,
        context: CommandContext,
    ) -> CommandResult:
        help_text = """
# Claude Code Python - Commands

## Basic Commands

| Command | Description |
|---------|-------------|
| `/help` | Show this help message |
| `/clear` | Clear conversation history |
| `/model <name>` | Switch to a different model |
| `/cost` | Show session costs and usage |
| `/stats` | Show session statistics |
| `/exit` | Exit Claude Code |

## Tips

- Commands can be abbreviated (e.g., `/h` for `/help`)
- Some commands accept arguments after the command name
        """
        return CommandResult(content=help_text)


class ClearCommand(Command):
    """Clear conversation history."""
    
    def __init__(self):
        super().__init__(
            name="clear",
            description="Clear conversation history",
            aliases=["reset"],
        )
    
    async def execute(
        self,
        args: str,
        context: CommandContext,
    ) -> CommandResult:
        if context.engine:
            context.engine.clear()
        
        context.console.print("[dim]Conversation cleared[/dim]")
        return CommandResult(is_silent=True)

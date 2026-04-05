"""
Claude Code Python - Clear Command
Clear conversation history.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from claude_code.commands.base import Command

if TYPE_CHECKING:
    from claude_code.repl import REPL


class ClearCommand(Command):
    """Clear the conversation history.
    
    Resets the conversation state while keeping the session active.
    Aliases: reset
    """
    
    name: str = "clear"
    aliases: list[str] = ["reset"]
    help_text: str = "Clear conversation history"
    
    async def execute(self, repl: REPL, args: str) -> bool:
        """Execute the clear command.
        
        Args:
            repl: The REPL instance.
            args: Command arguments (unused).
            
        Returns:
            True to continue running the REPL.
        """
        repl.engine.clear()
        repl.console.print("[dim]Conversation cleared[/dim]")
        return True

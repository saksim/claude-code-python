"""
Claude Code Python - Exit Command
Exit the REPL.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from claude_code.commands.base import Command

if TYPE_CHECKING:
    from claude_code.repl import REPL


class ExitCommand(Command):
    """Exit the Claude Code REPL.
    
    Exits the interactive session cleanly.
    Aliases: quit, q
    """
    
    name: str = "exit"
    aliases: list[str] = ["quit", "q"]
    help_text: str = "Exit Claude Code"
    
    async def execute(self, repl: REPL, args: str) -> bool:
        """Execute the exit command.
        
        Args:
            repl: The REPL instance.
            args: Command arguments (unused).
            
        Returns:
            False to stop the REPL loop.
        """
        repl.console.print("[dim]Goodbye![/dim]")
        repl._running = False
        return True

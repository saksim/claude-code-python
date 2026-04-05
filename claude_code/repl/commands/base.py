"""
Claude Code Python - Base Command
Base class for REPL commands.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from claude_code.repl import REPL


class Command(ABC):
    """Base class for REPL commands.
    
    Provides the interface that all REPL commands must implement.
    
    Attributes:
        name: The primary name of the command.
        aliases: Alternative names for the command.
        help_text: Description of the command for help display.
    """
    
    name: str
    aliases: list[str] = []
    help_text: str = ""
    
    @abstractmethod
    async def execute(self, repl: REPL, args: str) -> bool:
        """Execute the command.
        
        Args:
            repl: The REPL instance.
            args: Command arguments.
            
        Returns:
            True to continue the REPL loop, False to exit.
        """
        pass
    
    def get_commands(self) -> dict[str, Command]:
        """Get a dict of command name -> command for all aliases.
        
        Returns:
            Dictionary mapping command strings to this command instance.
        """
        commands: dict[str, Command] = {f"/{self.name}": self}
        for alias in self.aliases:
            commands[f"/{alias}"] = self
        return commands


class SimpleCommand(Command):
    """Command that executes a simple action.
    
    A convenience class for commands that wrap a simple callable.
    """
    
    def __init__(
        self,
        name: str,
        action: Callable[[REPL, str], Any],
        aliases: list[str] | None = None,
        help_text: str = "",
    ) -> None:
        """Initialize a simple command.
        
        Args:
            name: The command name.
            action: The callable to execute.
            aliases: Optional list of aliases.
            help_text: Optional help text.
        """
        self.name = name
        self._action = action
        self.aliases = aliases or []
        self.help_text = help_text
    
    async def execute(self, repl: REPL, args: str) -> bool:
        """Execute the simple action.
        
        Args:
            repl: The REPL instance.
            args: Command arguments.
            
        Returns:
            Result from the action callable.
        """
        return await self._action(repl, args)

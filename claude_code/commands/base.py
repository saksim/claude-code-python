"""
Claude Code Python - Command Base Classes

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Abstract base class pattern
- Dataclass for immutable data
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Awaitable

if TYPE_CHECKING:
    from rich.console import Console


class CommandType(Enum):
    """Command type classification.
    
    Attributes:
        PROMPT: Commands that modify the prompt
        LOCAL: Local commands that don't modify prompt
        LOCAL_JSX: Local JSX commands
    """
    PROMPT = "prompt"
    LOCAL = "local"
    LOCAL_JSX = "local-jsx"


@dataclass(frozen=True, slots=True)
class Command:
    """Base command definition.
    
    All commands inherit from this class and implement the execute method.
    
    Attributes:
        name: Command name (e.g., "status", "model")
        description: Human-readable command description
        command_type: Type of command (PROMPT, LOCAL, LOCAL_JSX)
        aliases: List of command aliases
        availability: List of availability conditions
        source: Command source (builtin, plugin, etc.)
    """
    name: str
    description: str
    command_type: CommandType = CommandType.PROMPT
    aliases: list[str] = field(default_factory=list)
    availability: list[str] = field(default_factory=list)
    source: str = "builtin"
    
    @abstractmethod
    async def execute(
        self,
        args: str,
        context: "CommandContext",
    ) -> "CommandResult":
        """Execute the command.
        
        Args:
            args: Command arguments
            context: Execution context
            
        Returns:
            CommandResult with execution output
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError


class SimpleCommand(Command):
    """Simple command that wraps a handler function.
    
    This is a convenience class for commands that just execute
    a simple handler function.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        handler: Callable[[str, "CommandContext"], Awaitable["CommandResult"]],
        command_type: CommandType = CommandType.LOCAL,
    ) -> None:
        """Initialize the simple command.
        
        Args:
            name: Command name
            description: Command description
            handler: Async function to handle execution
            command_type: Type of command
        """
        super().__init__(
            name=name,
            description=description,
            command_type=command_type,
        )
        self._handler = handler
    
    async def execute(
        self,
        args: str,
        context: "CommandContext",
    ) -> "CommandResult":
        """Execute the command using the handler.
        
        Args:
            args: Command arguments
            context: Execution context
            
        Returns:
            CommandResult from handler
        """
        return await self._handler(args, context)


@dataclass(frozen=True, slots=True)
class CommandContext:
    """Context available during command execution.
    
    Attributes:
        working_directory: Current working directory
        console: Rich console for output
        engine: Optional query engine
        session: Optional session
        config: Optional configuration
    """
    working_directory: str
    console: "Console"
    engine: Optional[Any] = None
    session: Optional[Any] = None
    config: Optional[Any] = None


@dataclass(frozen=True, slots=True)
class CommandResult:
    """Result from command execution."""
    success: bool = True
    content: Optional[str] = None
    error: Optional[str] = None
    is_silent: bool = False

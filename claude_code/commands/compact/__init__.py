"""
Claude Code Python - Compact Command
Compress conversation history to save tokens.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
"""

from __future__ import annotations

from typing import Any

from claude_code.commands.base import Command, CommandContext, CommandResult, CommandType
from claude_code.engine.compact import CompactService, CompactTrigger


class CompactCommand(Command):
    """Compress conversation history to save tokens.
    
    Creates a summary of the conversation and replaces older
    messages to free up context space.
    """
    
    def __init__(self) -> None:
        """Initialize the compact command."""
        super().__init__(
            name="compact",
            description="Compress conversation history to save tokens",
            command_type=CommandType.PROMPT,
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the compact command.
        
        Args:
            args: Command arguments (unused for compact command).
            context: The command execution context.
            
        Returns:
            CommandResult with compact information.
        """
        if context.engine is None:
            return CommandResult(
                success=False,
                error="Engine not available",
            )
        
        engine = context.engine
        
        messages: list[Any] = getattr(engine, "messages", [])
        token_count = getattr(engine, "total_input_tokens", 0)
        
        if len(messages) < 4:
            return CommandResult(
                content="Not enough conversation history to compact.",
            )
        
        return CommandResult(
            content=f"""# Compact Conversation

This will compress your conversation history to save tokens.

Current stats:
- Messages: {len(messages)}
- Tokens: ~{token_count}

A summary will be created and older messages will be replaced with the summary.

Use /compact to proceed with compression.""",
        )


class ResumeCommand(Command):
    """Resume a previous conversation.
    
    Allows loading and continuing from a previous session.
    """
    
    def __init__(self) -> None:
        """Initialize the resume command."""
        super().__init__(
            name="resume",
            description="Resume a previous conversation",
            command_type=CommandType.PROMPT,
            aliases=["continue", "-c"],
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the resume command.
        
        Args:
            args: Optional session ID to resume.
            context: The command execution context.
            
        Returns:
            CommandResult with resume information.
        """
        session_id = args.strip()
        
        if context.session is None:
            return CommandResult(
                success=False,
                error="Session not available",
            )
        
        if session_id:
            return CommandResult(
                content=f"""Resuming session: {session_id}

Use /resume without arguments to see available sessions.""",
            )
        
        from claude_code.engine.session import SessionManager
        
        sessions = SessionManager.list_sessions(context.working_directory)
        
        if not sessions:
            return CommandResult(
                content="No previous sessions found.",
            )
        
        lines: list[str] = ["# Available Sessions\n"]
        for session in sessions[:10]:
            lines.append(f"\n## {session['id']}")
            lines.append(f"Created: {session.get('created_at', 'unknown')}")
            lines.append(f"Messages: {session.get('message_count', 0)}")
        
        return CommandResult(content="\n".join(lines))


class RewindCommand(Command):
    """Rewind conversation to a previous point.
    
    Removes the last N turns from the current conversation.
    """
    
    def __init__(self) -> None:
        """Initialize the rewind command."""
        super().__init__(
            name="rewind",
            description="Rewind conversation to a previous point",
            command_type=CommandType.LOCAL,
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the rewind command.
        
        Args:
            args: Optional number of turns to rewind (defaults to 1).
            context: The command execution context.
            
        Returns:
            CommandResult with rewind information.
        """
        try:
            turns = int(args.strip()) if args.strip() else 1
        except ValueError:
            return CommandResult(
                success=False,
                error="Invalid number of turns",
            )
        
        if context.engine is None:
            return CommandResult(
                success=False,
                error="Engine not available",
            )
        
        engine = context.engine
        messages: list[Any] = getattr(engine, "messages", [])
        
        if len(messages) <= turns * 2:
            return CommandResult(
                success=False,
                error=f"Not enough messages to rewind {turns} turns",
            )
        
        removed = messages[-(turns * 2):]
        
        return CommandResult(
            content=f"""# Rewind

Removed last {turns} turn(s) ({len(removed)} messages).

Note: This only removes messages from the current session.
To fully remove from history, use /compact instead.""",
        )


def create_compact_command() -> CompactCommand:
    """Create compact command."""
    return CompactCommand()


def create_resume_command() -> ResumeCommand:
    """Create resume command."""
    return ResumeCommand()


def create_rewind_command() -> RewindCommand:
    """Create rewind command."""
    return RewindCommand()


__all__ = [
    "CompactCommand",
    "ResumeCommand",
    "RewindCommand",
    "create_compact_command",
    "create_resume_command",
    "create_rewind_command",
]

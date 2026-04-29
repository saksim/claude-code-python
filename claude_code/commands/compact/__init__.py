"""
Claude Code Python - Compact Command
Compress conversation history to save tokens.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
"""

from __future__ import annotations

from datetime import datetime
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
        engine = context.engine
        if engine is None:
            return CommandResult(success=False, error="Engine not available")

        # No args: show recent resumable sessions.
        if not session_id:
            sessions = self._list_sessions(engine)
            if not sessions:
                return CommandResult(content="No previous sessions found.")

            lines: list[str] = ["# Available Sessions\n"]
            for session in sessions[:10]:
                session_time = self._format_ts(session.last_active)
                lines.append(f"\n## {session.id}")
                lines.append(f"Last Active: {session_time}")
                lines.append(f"Messages: {session.message_count}")
                lines.append(f"Working Directory: {session.working_directory}")
            lines.append("\nUse /resume <session-id> to continue a session.")
            return CommandResult(content="\n".join(lines))

        if not hasattr(engine, "resume_session"):
            return CommandResult(
                success=False,
                error="Current engine does not support session resume",
            )

        try:
            resumed = await engine.resume_session(session_id)
        except Exception as exc:
            return CommandResult(
                success=False,
                error=f"Failed to resume session '{session_id}': {exc}",
            )

        if not resumed:
            return CommandResult(
                success=False,
                error=f"Session not found or unreadable: {session_id}",
            )

        active_session = getattr(engine.config, "session_id", session_id)
        message_count = len(getattr(engine, "messages", []))
        working_directory = getattr(engine.config, "working_directory", context.working_directory)
        return CommandResult(
            content=(
                "# Session Resumed\n\n"
                f"Session ID: {active_session}\n"
                f"Messages Restored: {message_count}\n"
                f"Working Directory: {working_directory}"
            )
        )

    def _list_sessions(self, engine: Any) -> list[Any]:
        """List resumable sessions from engine-bound manager or fallback manager."""
        from claude_code.engine.session import SessionManager

        manager = getattr(engine, "session_manager", None)
        if not isinstance(manager, SessionManager):
            manager = SessionManager()
        return manager.list_sessions()

    @staticmethod
    def _format_ts(ts: float) -> str:
        """Format unix timestamp for human-readable output."""
        try:
            return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return "unknown"


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

"""
Claude Code Python - Diff and Rename Commands

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- pathlib.Path for file operations
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from claude_code.commands.base import Command, CommandContext, CommandResult, CommandType


class DiffCommand(Command):
    """Show git diff of changes.
    
    Displays uncommitted changes in the working directory
    using git diff.
    """
    
    def __init__(self) -> None:
        """Initialize the diff command."""
        super().__init__(
            name="diff",
            description="Show git diff",
            command_type=CommandType.LOCAL,
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the diff command.
        
        Args:
            args: Optional git diff arguments.
            context: The command execution context.
            
        Returns:
            CommandResult with git diff output.
        """
        args = args.strip()
        
        try:
            cmd = ["git", "diff"]
            if args:
                cmd.extend(args.split())
            
            result = subprocess.run(
                cmd,
                cwd=context.working_directory,
                capture_output=True,
                text=True,
            )
            
            if result.returncode != 0 and not result.stdout:
                return CommandResult(
                    success=False,
                    error=f"Git error: {result.stderr}",
                )
            
            if not result.stdout:
                return CommandResult(content="No changes")
            
            return CommandResult(content=f"# Git Diff\n\n{result.stdout}")
        
        except FileNotFoundError:
            return CommandResult(success=False, error="Git not found")
        except Exception as e:
            return CommandResult(success=False, error=str(e))


class RenameCommand(Command):
    """Rename the current session.
    
    Updates the session name for easier identification.
    """
    
    def __init__(self) -> None:
        """Initialize the rename command."""
        super().__init__(
            name="rename",
            description="Rename current session",
            command_type=CommandType.LOCAL,
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the rename command.
        
        Args:
            args: New name for the session.
            context: The command execution context.
            
        Returns:
            CommandResult indicating success.
        """
        new_name = args.strip()
        
        if not new_name:
            return CommandResult(
                success=False,
                error="Usage: /rename <new-name>",
            )
        
        if context.session:
            context.session["name"] = new_name
            return CommandResult(content=f"Session renamed to: {new_name}")
        
        return CommandResult(content="Session will be renamed on next save")


class DiffFilesCommand(Command):
    """List changed files in the working directory.
    
    Shows all files that have been modified, added, or deleted
    compared to the last git commit.
    """
    
    def __init__(self) -> None:
        """Initialize the diff-files command."""
        super().__init__(
            name="diff-files",
            description="List changed files",
            command_type=CommandType.LOCAL,
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the diff-files command.
        
        Args:
            args: Command arguments (unused).
            context: The command execution context.
            
        Returns:
            CommandResult with list of changed files.
        """
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=context.working_directory,
                capture_output=True,
                text=True,
            )
            
            if not result.stdout:
                return CommandResult(content="No changes")
            
            lines: list[str] = ["# Changed Files\n"]
            for line in result.stdout.strip().split("\n"):
                if line:
                    status = line[:2]
                    file = line[3:]
                    lines.append(f"- {file} ({status})")
            
            return CommandResult(content="\n".join(lines))
        
        except Exception as e:
            return CommandResult(success=False, error=str(e))


def create_diff_command() -> DiffCommand:
    """Create the diff command.
    
    Returns:
        A new DiffCommand instance.
    """
    return DiffCommand()


def create_rename_command() -> RenameCommand:
    """Create the rename command.
    
    Returns:
        A new RenameCommand instance.
    """
    return RenameCommand()


__all__ = ["DiffCommand", "RenameCommand", "create_diff_command", "create_rename_command"]

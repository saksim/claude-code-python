"""
Claude Code Python - Branch Command

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
"""

from __future__ import annotations

import subprocess

from claude_code.commands.base import Command, CommandContext, CommandResult, CommandType


class BranchCommand(Command):
    """Manage git branches.
    
    Provides subcommands to list, create, switch to, and delete branches.
    Aliases: branches
    """
    
    def __init__(self) -> None:
        """Initialize the branch command."""
        super().__init__(
            name="branch",
            description="Git branch management",
            command_type=CommandType.LOCAL,
            aliases=["branches"],
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the branch command.
        
        Args:
            args: Command arguments (subcommand and its args).
            context: The command execution context.
            
        Returns:
            CommandResult with subcommand output.
        """
        args = args.strip()
        
        if not args:
            return await self._list_branches(context)
        
        parts = args.split()
        subcmd = parts[0]
        
        if subcmd == "list":
            return await self._list_branches(context)
        
        if subcmd == "create":
            if len(parts) < 2:
                return CommandResult(success=False, error="Usage: /branch create <name>")
            return await self._create_branch(parts[1], context)
        
        if subcmd == "switch":
            if len(parts) < 2:
                return CommandResult(success=False, error="Usage: /branch switch <name>")
            return await self._switch_branch(parts[1], context)
        
        if subcmd == "delete":
            if len(parts) < 2:
                return CommandResult(success=False, error="Usage: /branch delete <name>")
            return await self._delete_branch(" ".join(parts[1:]), context)
        
        return CommandResult(success=False, error=f"Unknown: {subcmd}")
    
    async def _list_branches(self, context: CommandContext) -> CommandResult:
        """List all git branches.
        
        Args:
            context: The command execution context.
            
        Returns:
            CommandResult with branch list.
        """
        try:
            result = subprocess.run(
                ["git", "branch", "-a"],
                cwd=context.working_directory,
                capture_output=True,
                text=True,
            )
            
            if result.returncode != 0:
                return CommandResult(success=False, error=result.stderr)
            
            lines: list[str] = ["# Branches\n"]
            for line in result.stdout.strip().split("\n"):
                if line:
                    line = line.strip()
                    if line.startswith("*"):
                        lines.append(f"* {line[2:]}")
                    else:
                        lines.append(f"  {line}")
            
            return CommandResult(content="\n".join(lines))
        
        except Exception as e:
            return CommandResult(success=False, error=str(e))
    
    async def _create_branch(self, name: str, context: CommandContext) -> CommandResult:
        """Create and switch to a new branch.
        
        Args:
            name: Name for the new branch.
            context: The command execution context.
            
        Returns:
            CommandResult indicating success.
        """
        try:
            result = subprocess.run(
                ["git", "checkout", "-b", name],
                cwd=context.working_directory,
                capture_output=True,
                text=True,
            )
            
            if result.returncode != 0:
                return CommandResult(success=False, error=result.stderr)
            
            return CommandResult(content=f"Created and switched to branch: {name}")
        
        except Exception as e:
            return CommandResult(success=False, error=str(e))
    
    async def _switch_branch(self, name: str, context: CommandContext) -> CommandResult:
        """Switch to an existing branch.
        
        Args:
            name: Name of the branch to switch to.
            context: The command execution context.
            
        Returns:
            CommandResult indicating success.
        """
        try:
            result = subprocess.run(
                ["git", "checkout", name],
                cwd=context.working_directory,
                capture_output=True,
                text=True,
            )
            
            if result.returncode != 0:
                return CommandResult(success=False, error=result.stderr)
            
            return CommandResult(content=f"Switched to branch: {name}")
        
        except Exception as e:
            return CommandResult(success=False, error=str(e))
    
    async def _delete_branch(self, name: str, context: CommandContext) -> CommandResult:
        """Delete a branch.
        
        Args:
            name: Name of the branch to delete.
            context: The command execution context.
            
        Returns:
            CommandResult indicating success.
        """
        try:
            result = subprocess.run(
                ["git", "branch", "-d", name],
                cwd=context.working_directory,
                capture_output=True,
                text=True,
            )
            
            if result.returncode != 0:
                return CommandResult(success=False, error=result.stderr)
            
            return CommandResult(content=f"Deleted branch: {name}")
        
        except Exception as e:
            return CommandResult(success=False, error=str(e))


def create_branch_command() -> BranchCommand:
    """Create the branch command.
    
    Returns:
        A new BranchCommand instance.
    """
    return BranchCommand()


__all__ = ["BranchCommand", "create_branch_command"]

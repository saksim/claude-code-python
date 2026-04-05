"""
Claude Code Python - Review Command

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
"""

from __future__ import annotations

from claude_code.commands.base import Command, CommandContext, CommandResult, CommandType


class ReviewCommand(Command):
    """Review code changes in the project.
    
    Provides interactive code review of git changes, modified files,
    or specific files mentioned by the user.
    """
    
    def __init__(self) -> None:
        """Initialize the review command."""
        super().__init__(
            name="review",
            description="Review code changes",
            command_type=CommandType.PROMPT,
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the review command.
        
        Args:
            args: Command arguments (unused for review command).
            context: The command execution context.
            
        Returns:
            CommandResult with review prompt.
        """
        return CommandResult(content="""# Code Review

I'll review the code changes in this session.

Please tell me what files or changes you'd like me to review, or I can check:

1. Recent git changes
2. Modified files in this session
3. Specific files you mention

What would you like me to review?""")
    
    def get_commands(self) -> dict[str, Command]:
        """Get command mappings including aliases."""
        commands: dict[str, Command] = {f"/{self.name}": self}
        for alias in self.aliases:
            commands[f"/{alias}"] = self
        return commands


def create_review_command() -> ReviewCommand:
    """Create the review command.
    
    Returns:
        A new ReviewCommand instance.
    """
    return ReviewCommand()


__all__ = ["ReviewCommand", "create_review_command"]

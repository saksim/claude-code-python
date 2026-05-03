"""
Claude Code Python - Review Command

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
"""

from __future__ import annotations

import shlex

from claude_code.commands.base import Command, CommandContext, CommandResult, CommandType
from claude_code.services.review_service import ReviewResult, ReviewService, ReviewServiceError


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
            command_type=CommandType.LOCAL,
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the review command.
        
        Args:
            args: Optional file paths (space separated, supports quoted paths).
            context: The command execution context.
            
        Returns:
            CommandResult with structured review findings.
        """
        review_service = ReviewService()
        cleaned_args = args.strip()

        try:
            if not cleaned_args:
                result = review_service.review_git_changes(context.working_directory)
                return CommandResult(content=self._render_result(result, "current git diff"))

            targets = shlex.split(cleaned_args)
            if not targets:
                return CommandResult(success=False, error="Usage: /review [file1 file2 ...]")

            result = review_service.review_files(context.working_directory, targets)
            return CommandResult(content=self._render_result(result, "specified files"))
        except ReviewServiceError as exc:
            return CommandResult(success=False, error=str(exc))
        except ValueError as exc:
            return CommandResult(success=False, error=f"Invalid arguments: {exc}")
        except Exception as exc:
            return CommandResult(success=False, error=f"Review failed: {exc}")

    def _render_result(self, result: ReviewResult, scope_label: str) -> str:
        """Render structured review result as markdown output."""
        lines: list[str] = [
            "# Code Review",
            "",
            f"Scope: {scope_label}",
            f"Files Reviewed: {len(result.files_reviewed)}",
            f"Findings: {len(result.findings)}",
        ]

        if not result.files_reviewed and result.scope == "git_diff":
            lines.extend(
                [
                    "",
                    "No changes found to review.",
                    "",
                    "Tip: modify files and run `/review` again, or run `/review <file>` for explicit paths.",
                ]
            )
            return "\n".join(lines)

        if result.warnings:
            lines.extend(["", "## Warnings"])
            for warning in result.warnings:
                lines.append(f"- {warning}")

        if not result.findings:
            lines.extend(["", "No findings detected in the reviewed scope."])
            return "\n".join(lines)

        lines.extend(["", "## Findings"])
        for index, finding in enumerate(result.findings, start=1):
            lines.extend(
                [
                    "",
                    f"{index}. [{finding.severity.upper()}] {finding.file_path}:{finding.line}",
                    f"   - Issue: {finding.issue}",
                    f"   - Recommendation: {finding.recommendation}",
                ]
            )

        return "\n".join(lines)


def create_review_command() -> ReviewCommand:
    """Create the review command.
    
    Returns:
        A new ReviewCommand instance.
    """
    return ReviewCommand()


__all__ = ["ReviewCommand", "create_review_command"]

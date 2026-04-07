"""
Claude Code Python - Suggest Background PR Tool

Suggests creating a background pull request for long-running tasks.

Following TOP Python Dev standards:
- Frozen dataclasses for immutable configs
- Clear type hints
- Comprehensive docstrings
"""

from __future__ import annotations

from typing import Any

from claude_code.tools.base import Tool, ToolResult
from claude_code.tools.base import ToolDefinition, ToolContext


class SuggestBackgroundPRTool(Tool):
    """Suggest creating a background PR for long-running tasks.
    
    This tool recommends when a task should be run in background
    and submitted as a pull request rather than running inline.
    
    Attributes:
        name: Tool name
        description: Tool description
        input_schema: JSON schema for tool input
    """
    
    def __init__(self) -> None:
        self._name = "suggest_background_pr"
        self._description = (
            "Suggest creating a background PR for long-running tasks"
        )
        self._input_schema = {
            "type": "object",
            "properties": {
                "task_description": {
                    "type": "string",
                    "description": "Description of the proposed task",
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for suggesting background PR",
                },
            },
            "required": ["task_description"],
        }
    
    @property
    def name(self) -> str:
        """Tool name."""
        return self._name
    
    @property
    def description(self) -> str:
        """Human-readable description."""
        return self._description
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input."""
        return self._input_schema
    
    def get_definition(self) -> ToolDefinition:
        """Get tool definition."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
        )
    
    async def execute(
        self,
        params: dict[str, Any],
        context: ToolContext,
    ) -> ToolResult:
        """Execute the tool.
        
        Args:
            params: Tool parameters
            context: Tool execution context
            
        Returns:
            ToolResult with suggestion
        """
        task_description = params.get("task_description", "")
        reason = params.get("reason", "")
        
        if not task_description:
            return ToolResult(
                tool_name=self._name,
                content="Error: task_description is required",
                is_error=True,
            )
        
        content = "## Background PR Suggestion\n\n"
        content += f"**Task**: {task_description}\n\n"
        
        if reason:
            content += f"**Reason**: {reason}\n\n"
        
        content += "### Recommended Approach\n"
        content += "1. Create a branch for this task\n"
        content += "2. Implement the feature in a focused PR\n"
        content += "3. Add tests for the new functionality\n"
        content += "4. Request review when ready\n\n"
        content += "This approach allows for:\n"
        content += "- Independent testing\n"
        content += "- Code review before merge\n"
        content += "- Rollback capability if needed\n"
        
        return ToolResult(
            tool_name=self._name,
            content=content,
            is_error=False,
        )


__all__ = ["SuggestBackgroundPRTool"]
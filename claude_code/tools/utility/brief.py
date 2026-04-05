"""
Claude Code Python - Brief Tool
Summarize content briefly.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Constants for defaults
"""

from __future__ import annotations

from typing import Any, Optional

from claude_code.tools.base import Tool, ToolCallback, ToolContext, ToolResult


class BriefTool(Tool):
    """Tool to create a brief summary of content.
    
    Creates a concise summary of provided content up to a maximum length.
    """
    
    DEFAULT_MAX_LENGTH: int = 100
    
    @property
    def name(self) -> str:
        """Tool name."""
        return "brief"
    
    @property
    def description(self) -> str:
        """Human-readable description."""
        return "Create a brief summary of the provided content"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input."""
        return {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Content to summarize"
                },
                "max_length": {
                    "type": "integer",
                    "description": "Maximum summary length",
                    "default": 100
                }
            },
            "required": ["content"]
        }
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the brief tool.
        
        Args:
            input_data: Dictionary containing content and max_length
            context: Tool execution context
            on_progress: Optional callback for progress updates
            
        Returns:
            ToolResult with summarized content
        """
        content = input_data.get("content", "")
        max_length = input_data.get("max_length", self.DEFAULT_MAX_LENGTH)
        
        if not content:
            return ToolResult(content="Error: content is required", is_error=True)
        
        words = content.split()
        summary: list[str] = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 > max_length:
                break
            summary.append(word)
            current_length += len(word) + 1
        
        result = " ".join(summary)
        if len(words) > len(summary):
            result += "..."
        
        return ToolResult(content=result)

"""
Claude Code Python - Snip Tool
Create a snippet from code.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
"""

from __future__ import annotations

from typing import Any, Optional

from claude_code.tools.base import Tool, ToolCallback, ToolContext, ToolResult


class SnipTool(Tool):
    """Tool to create a code snippet.
    
    Formats code as a markdown code block with language identifier.
    """
    
    DEFAULT_LANGUAGE = "plaintext"
    
    @property
    def name(self) -> str:
        return "snip"
    
    @property
    def description(self) -> str:
        return "Create a code snippet for sharing or reference"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Code to create snippet from"
                },
                "language": {
                    "type": "string",
                    "description": "Programming language",
                    "default": "plaintext"
                }
            },
            "required": ["code"]
        }
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the snip tool.
        
        Args:
            input_data: Dictionary containing code and language
            context: Tool execution context
            on_progress: Optional callback for progress updates
            
        Returns:
            ToolResult with formatted code snippet
        """
        code = input_data.get("code", "")
        language = input_data.get("language", self.DEFAULT_LANGUAGE)
        
        if not code:
            return ToolResult(content="Error: code is required", is_error=True)
        
        lines = code.strip().split("\n")
        
        result = [
            f"```{language}",
            *lines,
            "```"
        ]
        
        return ToolResult(content="\n".join(result))

"""
Claude Code Python - Sleep Tool
Pause execution for a specified duration.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Constants for limits
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional

from claude_code.tools.base import Tool, ToolCallback, ToolContext, ToolResult


class SleepTool(Tool):
    """Tool to pause execution for a specified duration.
    
    Useful for rate limiting, polling, or introducing delays in workflows.
    """
    
    MAX_SLEEP_DURATION = 300
    
    @property
    def name(self) -> str:
        return "sleep"
    
    @property
    def description(self) -> str:
        return "Pause execution for a specified duration (in seconds)"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "duration": {
                    "type": "number",
                    "description": "Duration to sleep in seconds"
                }
            },
            "required": ["duration"]
        }
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the sleep tool.
        
        Args:
            input_data: Dictionary containing duration
            context: Tool execution context
            on_progress: Optional callback for progress updates
            
        Returns:
            ToolResult with confirmation message
        """
        duration = input_data.get("duration", 1)
        
        if duration > self.MAX_SLEEP_DURATION:
            return ToolResult(
                content=f"Sleep duration too long: {duration}s (max {self.MAX_SLEEP_DURATION}s)",
                is_error=True
            )
        
        await asyncio.sleep(duration)
        
        return ToolResult(content=f"Slept for {duration} seconds")

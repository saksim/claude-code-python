"""
Claude Code Python - Web Fetch Tool
Fetch content from a URL.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Proper error handling
"""

from __future__ import annotations

import urllib.error
import urllib.request
from typing import Any, Optional

from claude_code.tools.base import Tool, ToolCallback, ToolContext, ToolResult


class WebFetchTool(Tool):
    """Tool to fetch content from a URL.
    
    Fetches web page content and returns it as plain text.
    Supports optional prompt to extract specific information.
    """
    
    MAX_CONTENT_LENGTH = 100000
    DEFAULT_TIMEOUT = 30
    USER_AGENT = "Claude Code Python/1.0"
    
    @property
    def name(self) -> str:
        return "web_fetch"
    
    @property
    def description(self) -> str:
        return "Fetch the content of a webpage from a URL"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to fetch"
                },
                "prompt": {
                    "type": "string",
                    "description": "What to extract from the page"
                }
            },
            "required": ["url"]
        }
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the web fetch tool.
        
        Args:
            input_data: Dictionary containing url and optional prompt
            context: Tool execution context
            on_progress: Optional callback for progress updates
            
        Returns:
            ToolResult with fetched content or error message
        """
        url = input_data.get("url", "")
        
        if not url:
            return ToolResult(content="Error: url is required", is_error=True)
        
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": self.USER_AGENT}
            )
            
            with urllib.request.urlopen(request, timeout=self.DEFAULT_TIMEOUT) as response:
                content = response.read().decode("utf-8", errors="replace")
            
            if len(content) > self.MAX_CONTENT_LENGTH:
                content = content[:self.MAX_CONTENT_LENGTH] + "\n... (truncated)"
            
            return ToolResult(content=content)
            
        except urllib.error.HTTPError as e:
            return ToolResult(content=f"HTTP error: {e.code} {e.reason}", is_error=True)
        except urllib.error.URLError as e:
            return ToolResult(content=f"URL error: {e.reason}", is_error=True)
        except OSError as e:
            return ToolResult(content=f"Error fetching URL: {e}", is_error=True)

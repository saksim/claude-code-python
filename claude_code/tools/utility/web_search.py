"""
Claude Code Python - Web Search Tool
Search the web using Exa API.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Proper error handling with specific exceptions
"""

from __future__ import annotations

import os
from typing import Any, Optional

from claude_code.tools.base import Tool, ToolCallback, ToolContext, ToolResult


class WebSearchTool(Tool):
    """Tool to search the web using Exa search API.
    
    Provides web search capabilities with title, URL, and snippet results.
    Requires EXA_API_KEY environment variable to be set.
    """
    
    DEFAULT_NUM_RESULTS = 10
    MAX_SNIPPET_LENGTH = 200
    
    @property
    def name(self) -> str:
        return "web_search"
    
    @property
    def description(self) -> str:
        return "Search the web for information"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    
    def is_read_only(self) -> bool:
        return True
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the web search tool.
        
        Args:
            input_data: Dictionary containing query and num_results
            context: Tool execution context
            on_progress: Optional callback for progress updates
            
        Returns:
            ToolResult with search results or error message
        """
        query = input_data.get("query", "")
        
        if not query:
            return ToolResult(content="Error: query is required", is_error=True)
        
        try:
            from exa_py import Exa
        except ImportError:
            return ToolResult(
                content="Search error: exa-py not installed. Run: pip install exa-py",
                is_error=True
            )
        
        api_key = os.environ.get("EXA_API_KEY")
        if not api_key:
            return ToolResult(
                content="Search error: EXA_API_KEY not set. Please set your Exa API key.",
                is_error=True
            )
        
        try:
            exa = Exa(api_key)
            num_results = input_data.get("num_results", self.DEFAULT_NUM_RESULTS)
            results = exa.search(query, num_results=num_results)
            
            if not results.results:
                return ToolResult(content="No results found")
            
            lines: list[str] = [f"Search results for '{query}':", ""]
            
            for i, result in enumerate(results.results, 1):
                lines.append(f"{i}. {result.title}")
                lines.append(f"   {result.url}")
                if result.snippet:
                    snippet = result.snippet[:self.MAX_SNIPPET_LENGTH]
                    lines.append(f"   {snippet}...")
                lines.append("")
            
            return ToolResult(content="\n".join(lines))
            
        except OSError as e:
            return ToolResult(content=f"Search error: {e}", is_error=True)
        except Exception as e:
            return ToolResult(content=f"Search error: {e}", is_error=True)

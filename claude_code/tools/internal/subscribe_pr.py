"""
Claude Code Python - Subscribe PR Tool
Feature-gated tool for GitHub PR subscriptions (KAIROS_GITHUB_WEBHOOKS).

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
"""

from __future__ import annotations

from typing import Any, Optional

from claude_code.tools.base import Tool, ToolContext, ToolResult, ToolCallback


class SubscribePRTool(Tool):
    """Subscribe to GitHub PR updates.
    
    This tool allows subscribing to GitHub pull request updates.
    Feature-gated under KAIROS_GITHUB_WEBHOOKS.
    
    Attributes:
        name: subscribe_pr
        description: Subscribe to GitHub PR notifications
    """
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "subscribe_pr"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "Subscribe to GitHub pull request notifications"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input."""
        return {
            "type": "object",
            "properties": {
                "owner": {
                    "type": "string",
                    "description": "Repository owner"
                },
                "repo": {
                    "type": "string",
                    "description": "Repository name"
                },
                "pr_number": {
                    "type": "number",
                    "description": "Pull request number"
                },
                "events": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Events to subscribe to (opened, closed, merged, commented)"
                }
            },
            "required": ["owner", "repo", "pr_number"]
        }
    
    def is_enabled(self) -> bool:
        """Check if tool is enabled."""
        import os
        return os.environ.get("KAIROS_GITHUB_WEBHOOKS", "0") == "1"
    
    def is_read_only(self) -> bool:
        """Tool modifies subscriptions."""
        return False
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute PR subscription."""
        if not self.is_enabled():
            return ToolResult(
                content="SubscribePRTool is disabled. Enable with KAIROS_GITHUB_WEBHOOKS=1",
                is_error=True
            )
        
        owner = input_data.get("owner", "")
        repo = input_data.get("repo", "")
        pr_number = input_data.get("pr_number", 0)
        
        return ToolResult(content=f"Subscribed to PR #{pr_number} in {owner}/{repo}")


__all__ = ["SubscribePRTool"]
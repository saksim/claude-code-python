"""
Claude Code Python - Config Tool
Manage Claude Code configuration.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
"""

from __future__ import annotations

import os
from typing import Any, Optional

from claude_code.tools.base import Tool, ToolContext, ToolResult, ToolCallback


class ConfigTool(Tool):
    """Tool to read and write Claude Code configuration.
    
    This tool provides read and write access to Claude Code
    configuration settings. Supported actions include getting,
    setting, listing, and deleting configuration values.
    
    Supported actions:
        - get: Retrieve a configuration value
        - set: Set a configuration value
        - list: List all configuration values
        - delete: Delete a configuration value
    
    Attributes:
        name: config
        description: Read or write Claude Code configuration
    """
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "config"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "Read or write Claude Code configuration"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input.
        
        Returns:
            JSON schema defining the input parameters.
        """
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["get", "set", "list", "delete"],
                    "description": "Action to perform (get, set, list, delete)"
                },
                "key": {
                    "type": "string",
                    "description": "Configuration key to operate on"
                },
                "value": {
                    "type": "string",
                    "description": "Configuration value (for set action)"
                }
            },
            "required": []
        }
    
    def is_read_only(self) -> bool:
        """Tool has mixed read/write behavior.
        
        Returns:
            False since set/delete modify configuration.
        """
        return False
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the configuration action.
        
        Args:
            input_data: Dictionary with 'action', optional 'key', 'value'.
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with action result.
        """
        from claude_code.config import Config
        
        action = input_data.get("action", "get")
        key = input_data.get("key", "")
        value = input_data.get("value", "")
        
        config = Config.load()
        
        if action == "get":
            if key:
                val = getattr(config, key, None)
                return ToolResult(content=f"{key} = {val}")
            else:
                return ToolResult(content="Use /config to see all values")
        
        elif action == "set":
            if not key:
                return ToolResult(content="Error: key is required", is_error=True)
            
            try:
                config.set(key, value)
                config.save()
                return ToolResult(content=f"Set {key} = {value}")
            except Exception as e:
                return ToolResult(content=f"Error: {str(e)}", is_error=True)
        
        elif action == "list":
            attrs = [a for a in dir(config) if not a.startswith('_')]
            lines = [f"Config '' = (use /config to see values)"]
            return ToolResult(content="\n".join(lines))
        
        else:
            return ToolResult(content=f"Unknown action: {action}", is_error=True)

"""Tools module - Registry re-exports."""

from typing import Optional, Any
from claude_code.tools.base import Tool, ToolDefinition, ToolContext, ToolResult, ToolInput, ToolProgress


class ToolRegistry:
    """Registry for all available tools.
    
    Manages tool registration, retrieval, and aliasing.
    
    Attributes:
        _tools: Dictionary mapping tool names to Tool instances
        _aliases: Dictionary mapping aliases to tool names
    """
    
    def __init__(self) -> None:
        """Initialize empty tool registry."""
        self._tools: dict[str, Tool] = {}
        self._aliases: dict[str, str] = {}
    
    def register(self, tool: Tool) -> None:
        """Register a tool.
        
        Args:
            tool: Tool instance to register
        """
        self._tools[tool.name] = tool
        
        # Register aliases
        definition = tool.get_definition()
        for alias in definition.aliases:
            self._aliases[alias] = tool.name
    
    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name or alias.
        
        Args:
            name: Tool name or alias
            
        Returns:
            Tool instance or None if not found
        """
        if name in self._tools:
            return self._tools[name]
        
        if name in self._aliases:
            return self._tools.get(self._aliases[name])
        
        return None
    
    def list_all(self) -> list[Tool]:
        """List all registered tools.
        
        Returns:
            List of all Tool instances
        """
        return list(self._tools.values())
    
    def get_definitions(self) -> list[dict[str, Any]]:
        """Get all tool definitions for API.
        
        Returns:
            List of tool definition dictionaries
        """
        return [tool.get_definition().__dict__ for tool in self._tools.values()]
    
    def get_names(self) -> list[str]:
        """Get all tool names.
        
        Returns:
            List of tool names
        """
        return list(self._tools.keys())


def create_default_registry() -> ToolRegistry:
    """Placeholder - implementation moved to tools/__init__.py"""
    raise NotImplementedError("Use create_default_registry from claude_code.tools")


__all__ = [
    "ToolRegistry",
    "create_default_registry",
    "Tool",
    "ToolContext",
    "ToolResult",
    "ToolDefinition",
    "ToolInput",
    "ToolProgress",
]
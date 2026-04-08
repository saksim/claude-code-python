"""Tools module - Registry re-exports."""

from typing import Optional, Any, Callable
from claude_code.tools.base import Tool, ToolDefinition, ToolContext, ToolResult, ToolInput, ToolProgress


class ToolRegistry:
    """Registry for all available tools.
    
    Manages tool registration, retrieval, and aliasing.
    Supports lazy loading - tools are only instantiated when accessed.
    
    Attributes:
        _tools: Dictionary mapping tool names to Tool instances (or factories)
        _aliases: Dictionary mapping aliases to tool names
        _lazy_factories: Dictionary mapping tool names to factory functions
    """
    
    def __init__(self, lazy: bool = True) -> None:
        """Initialize tool registry.
        
        Args:
            lazy: If True, tools are loaded lazily on first access.
        """
        self._tools: dict[str, Tool | None] = {}
        self._aliases: dict[str, str] = {}
        self._lazy_factories: dict[str, Callable[[], Tool]] = {}
        self._lazy = lazy
    
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
    
    def register_lazy(self, name: str, factory: Callable[[], Tool], aliases: list[str] = None) -> None:
        """Register a tool factory for lazy loading.
        
        Args:
            name: Tool name
            factory: Factory function that creates the tool instance
            aliases: Optional list of aliases for the tool
        """
        self._lazy_factories[name] = factory
        self._tools[name] = None  # Placeholder until first access
        
        if aliases:
            for alias in aliases:
                self._aliases[alias] = name
    
    def _resolve_tool(self, name: str) -> Optional[Tool]:
        """Resolve a lazy-loaded tool if needed.
        
        Args:
            name: Tool name to resolve
            
        Returns:
            Tool instance or None if not found
        """
        if name not in self._tools:
            # Check if we have a lazy factory for this
            if name in self._lazy_factories:
                self._tools[name] = self._lazy_factories[name]()
                del self._lazy_factories[name]  # No longer needed
            else:
                return None
        
        # Check if it's a lazy placeholder
        tool = self._tools[name]
        if tool is None and name in self._lazy_factories:
            tool = self._lazy_factories[name]()
            self._tools[name] = tool
            del self._lazy_factories[name]
        
        return tool
    
    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name or alias.
        
        Args:
            name: Tool name or alias
            
        Returns:
            Tool instance or None if not found
        """
        # Direct lookup in tools
        if name in self._tools:
            tool = self._tools[name]
            if tool is not None:
                return tool
            # Lazy load if needed
            return self._resolve_tool(name)
        
        # Check aliases
        if name in self._aliases:
            real_name = self._aliases[name]
            return self._resolve_tool(real_name)
        
        # Try lazy resolution
        if name in self._lazy_factories:
            return self._resolve_tool(name)
        
        return None
    
    def preload(self) -> None:
        """Preload all lazy tools (for eager initialization when needed)."""
        for name in list(self._lazy_factories.keys()):
            self._resolve_tool(name)
    
    def list_all(self) -> list[Tool]:
        """List all registered tools.
        
        Returns:
            List of all Tool instances
        """
        # Resolve all lazy tools first
        self.preload()
        return list(self._tools.values())
    
    def get_definitions(self) -> list[dict[str, Any]]:
        """Get all tool definitions for API.
        
        Returns:
            List of tool definition dictionaries
        """
        # Resolve all lazy tools first
        self.preload()
        return [tool.get_definition().__dict__ for tool in self._tools.values() if tool is not None]
    
    def get_names(self) -> list[str]:
        """Get all tool names.
        
        Returns:
            List of tool names
        """
        return list(self._tools.keys()) + list(self._lazy_factories.keys())


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
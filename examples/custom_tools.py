"""
Example: Custom Tool Creation
Shows how to create and register custom tools.
"""

import asyncio
from claude_code.tools import Tool, ToolContext, ToolResult, ToolRegistry
from claude_code.api.client import APIClient, APIClientConfig
from claude_code.engine.query import QueryEngine, QueryConfig


class CustomSearchTool(Tool):
    """Custom tool for searching a knowledge base."""
    
    @property
    def name(self) -> str:
        return "knowledge_search"
    
    @property
    def description(self) -> str:
        return "Search the internal knowledge base for documentation and examples."
    
    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                },
                "max_results": {
                    "type": "number",
                    "description": "Maximum number of results",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    
    async def execute(
        self,
        input_data: dict,
        context: ToolContext,
        on_progress=None,
    ) -> ToolResult:
        query = input_data["query"]
        max_results = input_data.get("max_results", 5)
        
        # Your search logic here
        results = [
            f"Found: {query} - Result 1",
            f"Found: {query} - Result 2",
        ]
        
        return ToolResult(
            content=f"Search results for '{query}':\n" + "\n".join(results[:max_results]),
            tool_use_id=""
        )


class FileAnalyzerTool(Tool):
    """Tool that analyzes code files."""
    
    @property
    def name(self) -> str:
        return "analyze_code"
    
    @property
    def description(self) -> str:
        return "Analyze code files for complexity, style issues, and suggestions."
    
    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the code file"
                },
                "check_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Types of checks to perform",
                    "enum": ["complexity", "style", "security", "all"]
                }
            },
            "required": ["file_path"]
        }
    
    def is_read_only(self) -> bool:
        return True
    
    async def execute(
        self,
        input_data: dict,
        context: ToolContext,
        on_progress=None,
    ) -> ToolResult:
        file_path = input_data["file_path"]
        check_types = input_data.get("check_types", ["all"])
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            lines = len(content.split('\n'))
            chars = len(content)
            
            return ToolResult(
                content=f"Analysis of {file_path}:\n"
                        f"- Lines: {lines}\n"
                        f"- Characters: {chars}\n"
                        f"- Checks: {', '.join(check_types)}",
                tool_use_id=""
            )
        except FileNotFoundError:
            return ToolResult(
                content=f"File not found: {file_path}",
                is_error=True,
                tool_use_id=""
            )


def create_custom_registry() -> ToolRegistry:
    """Create a registry with custom tools."""
    registry = ToolRegistry()
    
    # Add default tools
    from claude_code.tools import create_default_registry
    default = create_default_registry()
    for tool in default.list_all():
        registry.register(tool)
    
    # Add custom tools
    registry.register(CustomSearchTool())
    registry.register(FileAnalyzerTool())
    
    return registry


async def use_custom_tools():
    """Example using custom tools."""
    registry = create_custom_registry()
    
    # List all tools
    print("Available tools:")
    for name in registry.get_names():
        print(f"  - {name}")
    
    # Create engine with custom registry
    config = APIClientConfig()
    api_client = APIClient(config)
    
    engine = QueryEngine(
        api_client=api_client,
        config=QueryConfig(),
        tool_registry=registry,
    )
    
    # Query that might use custom tool
    async for event in engine.query(
        "Search the knowledge base for Python best practices"
    ):
        pass  # Handle events


if __name__ == "__main__":
    print("Custom tool example:")
    print("Run: python -m claude_code.main")

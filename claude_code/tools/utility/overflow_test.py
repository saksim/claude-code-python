"""
Claude Code Python - Overflow Test Tool

Tests for buffer overflow detection and handling.

Following TOP Python Dev standards:
- Frozen dataclasses for immutable configs
- Clear type hints
- Comprehensive docstrings

This tool is used for testing overflow conditions safely.
"""

from __future__ import annotations

from typing import Any

from claude_code.tools.base import Tool, ToolResult
from claude_code.tools.base import ToolDefinition, ToolContext


class OverflowTestTool(Tool):
    """Test tool for detecting and handling overflow conditions.
    
    This tool is primarily used for testing boundary conditions
    and ensuring the system handles extreme inputs gracefully.
    
    Attributes:
        name: Tool name
        description: Tool description
        input_schema: JSON schema for tool input
    """
    
    def __init__(self) -> None:
        self._name = "overflow_test"
        self._description = (
            "Test tool for detecting and handling overflow conditions"
        )
        self._input_schema = {
            "type": "object",
            "properties": {
                "test_type": {
                    "type": "string",
                    "description": "Type of overflow test to perform",
                    "enum": ["string", "array", "integer", "memory"],
                },
                "size": {
                    "type": "integer",
                    "description": "Size of the test data",
                },
            },
            "required": ["test_type"],
        }
    
    @property
    def name(self) -> str:
        """Tool name."""
        return self._name
    
    @property
    def description(self) -> str:
        """Human-readable description."""
        return self._description
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input."""
        return self._input_schema
    
    def get_definition(self) -> ToolDefinition:
        """Get tool definition."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
        )
    
    async def execute(
        self,
        params: dict[str, Any],
        context: ToolContext,
    ) -> ToolResult:
        """Execute the tool.
        
        Args:
            params: Tool parameters
            context: Tool execution context
            
        Returns:
            ToolResult with test results
        """
        test_type = params.get("test_type", "string")
        size = params.get("size", 1000)
        
        if test_type == "string":
            result = "x" * min(size, 10000)
            return ToolResult(
                tool_name=self._name,
                content=f"String overflow test: Created {len(result)} characters",
                is_error=False,
            )
        elif test_type == "array":
            result = list(range(min(size, 1000000)))
            return ToolResult(
                tool_name=self._name,
                content=f"Array overflow test: Created {len(result)} elements",
                is_error=False,
            )
        elif test_type == "integer":
            try:
                result = 2**min(size, 10000)
                return ToolResult(
                    tool_name=self._name,
                    content=f"Integer overflow test: 2^{min(size, 10000)} = {result}",
                    is_error=False,
                )
            except OverflowError:
                return ToolResult(
                    tool_name=self._name,
                    content="Integer overflow detected and handled safely",
                    is_error=False,
                )
        elif test_type == "memory":
            return ToolResult(
                tool_name=self._name,
                content=f"Memory test with size {size} not fully implemented - safe default",
                is_error=False,
            )
        else:
            return ToolResult(
                tool_name=self._name,
                content=f"Unknown test type: {test_type}",
                is_error=True,
            )


__all__ = ["OverflowTestTool"]
"""
Claude Code Python - Synthetic Output Tool

Generates synthetic/artificial output for testing and demonstration purposes.

Following TOP Python Dev standards:
- Frozen dataclasses for immutable configs
- Clear type hints
- Comprehensive docstrings
"""

from __future__ import annotations

from typing import Any, Optional

from claude_code.tools.base import Tool, ToolResult
from claude_code.tools.base import ToolDefinition, ToolContext


class SyntheticOutputTool(Tool):
    """Generate synthetic/artificial output for testing.
    
    This tool is used for generating mock outputs, test data,
    and placeholder content for development and testing purposes.
    
    Attributes:
        name: Tool name
        description: Tool description
        input_schema: JSON schema for tool input
    """
    
    def __init__(self) -> None:
        self._name = "synthetic_output"
        self._description = (
            "Generate synthetic/artificial output for testing and demonstration"
        )
        self._input_schema = {
            "type": "object",
            "properties": {
                "output_type": {
                    "type": "string",
                    "description": "Type of synthetic output to generate",
                    "enum": [
                        "json",
                        "xml",
                        "csv",
                        "markdown",
                        "html",
                        "lorem",
                        "code",
                    ],
                },
                "count": {
                    "type": "integer",
                    "description": "Number of items to generate",
                    "default": 1,
                },
                "template": {
                    "type": "string",
                    "description": "Template for generation",
                },
            },
            "required": ["output_type"],
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
            ToolResult with synthetic output
        """
        output_type = params.get("output_type", "json")
        count = params.get("count", 1)
        template = params.get("template", "")
        
        content = self._generate_output(output_type, count, template)
        
        return ToolResult(
            tool_name=self._name,
            content=content,
            is_error=False,
        )
    
    def _generate_output(
        self,
        output_type: str,
        count: int,
        template: str,
    ) -> str:
        """Generate synthetic output based on type."""
        
        if output_type == "json":
            items = [
                {"id": i, "name": f"Item {i}", "value": i * 100}
                for i in range(1, count + 1)
            ]
            import json
            return json.dumps({"data": items}, indent=2)
        
        elif output_type == "xml":
            items = "\n".join(
                f"  <item id='{i}'><name>Item {i}</name><value>{i * 100}</value></item>"
                for i in range(1, count + 1)
            )
            return f"<root>\n{items}\n</root>"
        
        elif output_type == "csv":
            lines = ["id,name,value"]
            for i in range(1, count + 1):
                lines.append(f"{i},Item {i},{i * 100}")
            return "\n".join(lines)
        
        elif output_type == "markdown":
            lines = ["# Synthetic Report", ""]
            for i in range(1, count + 1):
                lines.extend([
                    f"## Item {i}",
                    f"- **Name**: Item {i}",
                    f"- **Value**: {i * 100}",
                    "",
                ])
            return "\n".join(lines)
        
        elif output_type == "html":
            items = "\n".join(
                f"      <li>Item {i}: {i * 100}</li>"
                for i in range(1, count + 1)
            )
            return f"""<!DOCTYPE html>
<html>
<head><title>Synthetic Output</title></head>
<body>
  <h1>Items</h1>
  <ul>
{items}
  </ul>
</body>
</html>"""
        
        elif output_type == "lorem":
            lorem_text = (
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
                "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
            )
            return (lorem_text * count)[:500]
        
        elif output_type == "code":
            return self._generate_code(count, template)
        
        return f"Unknown output type: {output_type}"
    
    def _generate_code(self, count: int, template: str) -> str:
        """Generate synthetic code."""
        
        if template == "python":
            lines = [
                "# Synthetic Python Code",
                "",
                "class DataProcessor:",
                '    """Data processor class."""',
                "",
                "    def __init__(self):",
                "        self.data = []",
                "",
                "    def process(self, item):",
                "        return item * 2",
                "",
            ]
            return "\n".join(lines)
        
        elif template == "javascript":
            lines = [
                "// Synthetic JavaScript Code",
                "",
                "class DataProcessor {",
                "  constructor() {",
                "    this.data = [];",
                "  }",
                "",
                "  process(item) {",
                "    return item * 2;",
                "  }",
                "}",
                "",
            ]
            return "\n".join(lines)
        
        return f"// Synthetic code block ({count} items)"


__all__ = ["SyntheticOutputTool"]
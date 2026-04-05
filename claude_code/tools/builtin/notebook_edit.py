"""
Claude Code Python - Notebook Edit Tool
Edit Jupyter notebook cells.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
"""

from __future__ import annotations

import os
import json
from typing import Any, Optional

from claude_code.tools.base import Tool, ToolContext, ToolResult, ToolCallback


class NotebookEditTool(Tool):
    """Tool to edit Jupyter notebook cells.
    
    This tool provides functionality to edit individual cells within
    a Jupyter notebook (.ipynb) file. Users can modify cell content
    and cell type (code or markdown).
    
    Attributes:
        name: notebook_edit
        description: Edit a Jupyter notebook (.ipynb file)
    """
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "notebook_edit"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "Edit a Jupyter notebook (.ipynb file)"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input.
        
        Returns:
            JSON schema defining the input parameters.
        """
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the notebook file"
                },
                "cell_index": {
                    "type": "integer",
                    "description": "Cell index to edit (0-based)"
                },
                "source": {
                    "type": "string",
                    "description": "New cell content"
                },
                "cell_type": {
                    "type": "string",
                    "enum": ["code", "markdown"],
                    "description": "Cell type (code or markdown)",
                    "default": "code"
                }
            },
            "required": ["file_path", "cell_index"]
        }
    
    def is_read_only(self) -> bool:
        """Tool modifies system state by editing notebooks.
        
        Returns:
            False since this tool edits notebook files.
        """
        return False
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the notebook cell edit.
        
        Args:
            input_data: Dictionary with 'file_path', 'cell_index', 'source', 'cell_type'.
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with edit status.
        """
        file_path = input_data.get("file_path", "")
        cell_index = input_data.get("cell_index", 0)
        source = input_data.get("source", "")
        cell_type = input_data.get("cell_type", "code")
        
        if not file_path:
            return ToolResult(content="Error: file_path is required", is_error=True)
        
        if not os.path.isabs(file_path):
            file_path = os.path.join(context.working_directory, file_path)
        
        if not os.path.exists(file_path):
            return ToolResult(content=f"Notebook not found: {file_path}", is_error=True)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                notebook = json.load(f)
            
            if "cells" not in notebook:
                return ToolResult(content="Invalid notebook format", is_error=True)
            
            if cell_index >= len(notebook["cells"]):
                return ToolResult(content=f"Cell index out of range: {cell_index}", is_error=True)
            
            notebook["cells"][cell_index]["source"] = source
            if cell_type:
                notebook["cells"][cell_index]["cell_type"] = cell_type
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(notebook, f, indent=1)
            
            return ToolResult(content=f"Edited cell {cell_index} in {file_path}")
            
        except Exception as e:
            return ToolResult(content=f"Error: {str(e)}", is_error=True)

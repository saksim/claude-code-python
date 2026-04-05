"""
Claude Code Python - Plan Mode Tools
Manage plan mode and workflow execution.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
"""

from __future__ import annotations

from typing import Any, Optional

from claude_code.tools.base import Tool, ToolContext, ToolResult, ToolCallback


class EnterPlanModeTool(Tool):
    """Tool to enter plan mode.
    
    In plan mode, tool calls are shown for user approval
    before execution.
    """
    
    @property
    def name(self) -> str:
        """Tool name."""
        return "enter_plan_mode"
    
    @property
    def description(self) -> str:
        """Human-readable description."""
        return "Enter plan mode to review and approve tool calls before execution"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input."""
        return {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Reason for entering plan mode"
                }
            },
            "required": []
        }
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the enter plan mode tool.
        
        Args:
            input_data: Dictionary containing optional reason.
            context: Tool execution context.
            on_progress: Optional callback for progress updates.
            
        Returns:
            ToolResult confirming plan mode entry.
        """
        reason = input_data.get("reason", "")
        
        from claude_code.state.app_state import get_default_app_state
        state = get_default_app_state()
        
        state.tool_permission_context.mode = "plan"
        
        message = "Entered plan mode. Tool calls will be shown for approval before execution."
        if reason:
            message += f"\n\nReason: {reason}"
        
        return ToolResult(content=message)


class ExitPlanModeTool(Tool):
    """Tool to exit plan mode.
    
    Returns to normal automatic execution mode.
    """
    
    @property
    def name(self) -> str:
        """Tool name."""
        return "exit_plan_mode"
    
    @property
    def description(self) -> str:
        """Human-readable description."""
        return "Exit plan mode and return to normal execution"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input."""
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the exit plan mode tool.
        
        Args:
            input_data: Dictionary (unused).
            context: Tool execution context.
            on_progress: Optional callback for progress updates.
            
        Returns:
            ToolResult confirming plan mode exit.
        """
        from claude_code.state.app_state import get_default_app_state
        from claude_code.config import PermissionMode
        
        state = get_default_app_state()
        
        state.tool_permission_context.mode = PermissionMode.AUTO
        
        return ToolResult(content="Exited plan mode. Normal execution resumed.")


class WorkflowTool(Tool):
    """Tool to run a predefined workflow.
    
    Executes named workflows with provided parameters.
    """
    
    @property
    def name(self) -> str:
        """Tool name."""
        return "workflow"
    
    @property
    def description(self) -> str:
        """Human-readable description."""
        return "Run a predefined workflow"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input."""
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the workflow to run"
                },
                "params": {
                    "type": "object",
                    "description": "Workflow parameters"
                }
            },
            "required": ["name"]
        }
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the workflow tool.
        
        Args:
            input_data: Dictionary containing workflow name and params.
            context: Tool execution context.
            on_progress: Optional callback for progress updates.
            
        Returns:
            ToolResult with workflow execution status.
        """
        name = input_data.get("name", "")
        params: dict[str, Any] = input_data.get("params", {})
        
        if not name:
            return ToolResult(content="Error: workflow name required", is_error=True)
        
        return ToolResult(
            content=f"Workflow '{name}' not implemented.\nParams: {params}"
        )


__all__ = ["EnterPlanModeTool", "ExitPlanModeTool", "WorkflowTool"]

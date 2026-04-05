"""
Claude Code Python - Ask User Question Tool
Ask the user a question and get their response.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
"""

from __future__ import annotations

from typing import Any, Optional

from claude_code.tools.base import Tool, ToolContext, ToolResult, ToolCallback


class AskUserQuestionTool(Tool):
    """Tool to ask the user a question and get their response.
    
    This tool allows the AI to ask clarifying questions to the user
    during a conversation. It can provide predefined options or allow
    free-form responses.
    
    Attributes:
        name: ask_user_question
        description: Ask the user a question and return their response
    """
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "ask_user_question"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "Ask the user a question and return their response"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input.
        
        Returns:
            JSON schema defining the input parameters.
        """
        return {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "Question to ask the user"
                },
                "options": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional predefined options for the user to choose from"
                }
            },
            "required": ["question"]
        }
    
    def is_read_only(self) -> bool:
        """Tool only asks questions, doesn't modify state.
        
        Returns:
            True since asking questions is a read operation.
        """
        return True
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the user question.
        
        Args:
            input_data: Dictionary with 'question' and optional 'options'.
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with the question and options.
        """
        question = input_data.get("question", "")
        options = input_data.get("options", [])
        
        if not question:
            return ToolResult(content="Error: question is required", is_error=True)
        
        lines = [f"Question: {question}"]
        if options:
            lines.append("Options:")
            for i, opt in enumerate(options, 1):
                lines.append(f"  {i}. {opt}")
        else:
            lines.append("(This tool would prompt the user for input)")
        
        return ToolResult(content="\n".join(lines))

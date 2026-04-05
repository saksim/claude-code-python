"""
Claude Code Python - Ask User Question Tool
User interaction tool for asking questions with options.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Dataclass patterns
"""

from __future__ import annotations

from typing import Any, Optional, Union
from dataclasses import dataclass, field

from claude_code.tools.base import Tool, ToolContext, ToolResult, ToolCallback


@dataclass(frozen=True, slots=True)
class QuestionOption:
    """A single option for a user question.
    
    Using frozen=True, slots=True for immutability.
    
    Attributes:
        label: Display label for the option
        description: Optional description explaining the option
        value: Optional value to return if selected
    """
    label: str
    description: str = ""
    value: Optional[str] = None


@dataclass(frozen=True, slots=True)
class QuestionPreview:
    """Preview text for the question presentation.
    
    Using frozen=True, slots=True for immutability.
    
    Attributes:
        header: Optional header text to display
        options: List of available question options
        multi_select: Whether multiple options can be selected
    """
    header: str = ""
    options: tuple[QuestionOption, ...] = field(default_factory=tuple)
    multi_select: bool = False


class AskUserQuestionTool(Tool):
    """Ask user a question with predefined options.
    
    This tool allows the AI to present questions to the user with
    predefined answer options. Users select from these options rather
    than providing free-form responses.
    
    Attributes:
        name: ask_user_question
        description: Ask the user a question with predefined options
    """
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "ask_user_question"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "Ask the user a question with predefined options"
    
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
                    "description": "The question to ask the user"
                },
                "header": {
                    "type": "string",
                    "description": "Optional header text to display above the question"
                },
                "options": {
                    "type": "array",
                    "description": "Array of answer options",
                    "items": {
                        "type": "object",
                        "properties": {
                            "label": {"type": "string", "description": "Display label for option"},
                            "description": {"type": "string", "description": "Option description"},
                            "value": {"type": "string", "description": "Value to return if selected"}
                        },
                        "required": ["label"]
                    }
                },
                "multi_select": {
                    "type": "boolean",
                    "description": "Allow the user to select multiple options",
                    "default": False
                }
            },
            "required": ["question", "options"]
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
            input_data: Dictionary with 'question', 'options', optional 'header', 'multi_select'.
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with the question and options.
        """
        question = input_data.get("question", "")
        header = input_data.get("header", "")
        options = input_data.get("options", [])
        multi_select = input_data.get("multi_select", False)
        
        if not question:
            return ToolResult(
                content="Error: question is required",
                is_error=True
            )
        
        if not options:
            return ToolResult(
                content="Error: at least one option is required",
                is_error=True
            )
        
        lines = [f"# {question}\n"]
        
        if header:
            lines.append(f"\n{header}\n")
        
        lines.append("\n## Options\n")
        
        for i, opt in enumerate(options, 1):
            label = opt.get("label", "")
            desc = opt.get("description", "")
            
            lines.append(f"{i}. **{label}**")
            if desc:
                lines.append(f"   {desc}")
            lines.append("")
        
        if multi_select:
            lines.append("\n*Multiple selections allowed*")
        
        lines.append("\n## Response Format")
        lines.append("Please select by number or description.")
        
        return ToolResult(content="\n".join(lines))


class AskFollowUpQuestionTool(Tool):
    """Ask follow-up questions based on previous answers.
    
    This tool allows the AI to ask a follow-up question that
    builds on a previous user response or context.
    
    Attributes:
        name: ask_follow_up
        description: Ask a follow-up question after user selects an option
    """
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "ask_follow_up"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "Ask a follow-up question after user selects an option"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input.
        
        Returns:
            JSON schema defining the input parameters.
        """
        return {
            "type": "object",
            "properties": {
                "context": {
                    "type": "string",
                    "description": "Previous context or answer to reference"
                },
                "question": {
                    "type": "string",
                    "description": "Follow-up question to ask the user"
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
        """Execute the follow-up question.
        
        Args:
            input_data: Dictionary with 'context' and 'question'.
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with the follow-up question.
        """
        context_prev = input_data.get("context", "")
        question = input_data.get("question", "")
        
        lines = ["# Follow-up Question\n"]
        
        if context_prev:
            lines.append(f"\n**Previous context:** {context_prev}\n")
        
        lines.append(f"\n{question}")
        
        return ToolResult(content="\n".join(lines))


__all__ = ["AskUserQuestionTool", "AskFollowUpQuestionTool"]

"""
Message formatting for Claude Code Python.

Provides functions for formatting different message types.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Dataclass patterns (frozen/slots)
- Optional rich library support with graceful fallback
"""

from __future__ import annotations

from typing import Optional, Any
from dataclasses import dataclass, field
from enum import Enum


try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.syntax import Syntax
    RICH_AVAILABLE: bool = True
except ImportError:
    RICH_AVAILABLE = False
    Markdown = None
    Syntax = None


# Message type enum
class MessageType(Enum):
    """Message types for Claude Code.
    
    Attributes:
        USER: User input messages
        ASSISTANT: AI assistant messages
        SYSTEM: System messages
        TOOL: Tool execution result messages
        ERROR: Error messages
    """
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class FormattedMessage:
    """A formatted message.
    
    Using frozen=True, slots=True for immutability and memory efficiency.
    
    Attributes:
        type: The message type
        content: The formatted content
        metadata: Additional message metadata
    """
    type: MessageType
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class MessageFormatter:
    """Formats messages for display.
    
    Handles different message types and their formatting.
    Supports markdown rendering and syntax highlighting when rich is available.
    
    Attributes:
        console: Optional rich Console for rich output
        use_markdown: Whether to render markdown
        use_syntax_highlighting: Whether to use syntax highlighting
    """
    
    def __init__(self, console: Optional[Any] = None):
        self.console = console
        self.use_markdown = True
        self.use_syntax_highlighting = True
    
    def format_user_message(self, content: str) -> FormattedMessage:
        """Format a user message.
        
        Args:
            content: User message content
            
        Returns:
            FormattedMessage with USER type.
        """
        return FormattedMessage(
            type=MessageType.USER,
            content=content,
        )
    
    def format_assistant_message(
        self,
        content: str,
        thinking: Optional[str] = None,
    ) -> FormattedMessage:
        """Format an assistant message.
        
        Args:
            content: Assistant message content
            thinking: Optional thinking/thought process to display
            
        Returns:
            FormattedMessage with ASSISTANT type.
        """
        formatted = content
        
        if thinking:
            formatted = f"[hidden thinking]\n{thinking}\n[/hidden thinking]\n\n{formatted}"
        
        return FormattedMessage(
            type=MessageType.ASSISTANT,
            content=formatted,
        )
    
    def format_system_message(self, content: str) -> FormattedMessage:
        """Format a system message.
        
        Args:
            content: System message content
            
        Returns:
            FormattedMessage with SYSTEM type.
        """
        return FormattedMessage(
            type=MessageType.SYSTEM,
            content=content,
        )
    
    def format_tool_result(
        self,
        tool_name: str,
        result: str,
        success: bool = True,
    ) -> FormattedMessage:
        """Format a tool result.
        
        Args:
            tool_name: Name of the tool that was executed
            result: Result from the tool execution
            success: Whether the tool succeeded
            
        Returns:
            FormattedMessage with TOOL type.
        """
        icon = "✓" if success else "✗"
        return FormattedMessage(
            type=MessageType.TOOL,
            content=f"{icon} {tool_name}\n{result}",
            metadata={"tool_name": tool_name, "success": success},
        )
    
    def format_error(self, error: str) -> FormattedMessage:
        """Format an error message.
        
        Args:
            error: Error message content
            
        Returns:
            FormattedMessage with ERROR type.
        """
        return FormattedMessage(
            type=MessageType.ERROR,
            content=error,
        )
    
    def render(self, message: FormattedMessage) -> str:
        """Render a formatted message to string.
        
        Args:
            message: FormattedMessage to render
            
        Returns:
            String content of the message.
        """
        return message.content
    
    def render_markdown(self, text: str) -> str:
        """Render markdown text.
        
        Args:
            text: Markdown text to render
            
        Returns:
            Rendered text string.
        """
        if self.use_markdown and RICH_AVAILABLE and Markdown:
            md = Markdown(text)
            return str(md)
        return text
    
    def render_code(
        self,
        code: str,
        language: str = "python",
    ) -> str:
        """Render code with syntax highlighting.
        
        Args:
            code: Code string to render
            language: Programming language for highlighting
            
        Returns:
            Rendered code string.
        """
        if self.use_syntax_highlighting and RICH_AVAILABLE and Syntax:
            syntax = Syntax(code, language)
            return str(syntax)
        return code


# Module-level formatting functions for convenience
def format_user_message(content: str) -> str:
    """Format a user message for display.
    
    Args:
        content: User message content
        
    Returns:
        Formatted string with user indicator.
    """
    return f"[bold cyan]You:[/bold cyan]\n{content}"


def format_assistant_message(
    content: str,
    thinking: Optional[str] = None,
) -> str:
    """Format an assistant message for display.
    
    Args:
        content: Assistant message content
        thinking: Optional thinking/thought process
        
    Returns:
        Formatted string, possibly with thinking preview.
    """
    if thinking:
        return f"[dim]Thinking...[/dim]\n\n{content}"
    return content


def format_system_message(content: str) -> str:
    """Format a system message for display.
    
    Args:
        content: System message content
        
    Returns:
        Formatted string with system indicator.
    """
    return f"[yellow]System:[/yellow]\n{content}"


def format_tool_result(
    tool_name: str,
    result: str,
    success: bool = True,
) -> str:
    """Format a tool result for display.
    
    Args:
        tool_name: Name of the executed tool
        result: Tool execution result
        success: Whether the tool succeeded
        
    Returns:
        Formatted string with success/failure indicator.
    """
    icon = "[green]✓[/green]" if success else "[red]✗[/red]"
    return f"{icon} [bold]{tool_name}[/bold]\n{result}"


def format_error(error: str) -> str:
    """Format an error message for display.
    
    Args:
        error: Error message content
        
    Returns:
        Formatted string with error indicator.
    """
    return f"[bold red]Error:[/bold red] {error}"


def format_code_block(
    code: str,
    language: str = "python",
    show_line_numbers: bool = True,
) -> str:
    """Format a code block.
    
    Args:
        code: Code string to format
        language: Programming language
        show_line_numbers: Whether to show line numbers
        
    Returns:
        Formatted code block string.
    """
    if RICH_AVAILABLE and Syntax:
        syntax = Syntax(
            code,
            language,
            line_numbers=show_line_numbers,
        )
        return str(syntax)
    return f"```{language}\n{code}\n```"


def format_file_diff(diff: str) -> str:
    """Format a file diff.
    
    Args:
        diff: Diff string to format
        
    Returns:
        Formatted diff with color-coded additions/deletions.
    """
    lines = diff.split('\n')
    formatted: list[str] = []
    
    for line in lines:
        if line.startswith('+'):
            formatted.append(f"[green]{line}[/green]")
        elif line.startswith('-'):
            formatted.append(f"[red]{line}[/red]")
        elif line.startswith('@@'):
            formatted.append(f"[blue]{line}[/blue]")
        else:
            formatted.append(line)
    
    return '\n'.join(formatted)

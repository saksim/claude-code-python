"""
UI components for Claude Code Python - Enhanced Rendering
Advanced terminal rendering components

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Dataclass patterns (frozen/slots)
- frozenset for constant sets
- Proper error handling
"""

from __future__ import annotations

import asyncio
import sys
from typing import Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


# Module-level constants using frozenset
_ANSI_RESET = "\033[0m"
_ANSI_BOLD = "\033[1m"
_ANSI_DIM = "\033[2m"
_ANSI_ITALIC = "\033[3m"
_ANSI_UNDERLINE = "\033[4m"

_ANSI_FOREGROUND = {
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
}

_ANSI_BACKGROUND = {
    "black": "\033[40m",
    "red": "\033[41m",
    "green": "\033[42m",
    "yellow": "\033[43m",
    "blue": "\033[44m",
    "magenta": "\033[45m",
    "cyan": "\033[46m",
    "white": "\033[47m",
}

_SPINNER_FRAMES = ("◐", "◑", "◒", "◓", "◑", "◐")

_STATUS_ICONS: dict[str, str] = {
    "success": "✓",
    "error": "✗",
    "warning": "⚠",
    "info": "ℹ",
    "loading": "◐",
    "pending": "○",
}

_STATUS_COLORS: dict[str, str] = {
    "success": _ANSI_FOREGROUND["green"],
    "error": _ANSI_FOREGROUND["red"],
    "warning": _ANSI_FOREGROUND["yellow"],
    "info": _ANSI_FOREGROUND["cyan"],
    "loading": _ANSI_FOREGROUND["cyan"],
    "pending": _ANSI_DIM,
}


class AnsiCode(Enum):
    """ANSI escape codes for terminal styling.
    
    Attributes:
        RESET: Reset all attributes
        BOLD: Bold text
        DIM: Dim text
        ITALIC: Italic text
        UNDERLINE: Underlined text
        BLACK through WHITE: Foreground colors
        BG_BLACK through BG_WHITE: Background colors
    """
    RESET = _ANSI_RESET
    BOLD = _ANSI_BOLD
    DIM = _ANSI_DIM
    ITALIC = _ANSI_ITALIC
    UNDERLINE = _ANSI_UNDERLINE
    
    BLACK = _ANSI_FOREGROUND["black"]
    RED = _ANSI_FOREGROUND["red"]
    GREEN = _ANSI_FOREGROUND["green"]
    YELLOW = _ANSI_FOREGROUND["yellow"]
    BLUE = _ANSI_FOREGROUND["blue"]
    MAGENTA = _ANSI_FOREGROUND["magenta"]
    CYAN = _ANSI_FOREGROUND["cyan"]
    WHITE = _ANSI_FOREGROUND["white"]
    
    BG_BLACK = _ANSI_BACKGROUND["black"]
    BG_RED = _ANSI_BACKGROUND["red"]
    BG_GREEN = _ANSI_BACKGROUND["green"]
    BG_YELLOW = _ANSI_BACKGROUND["yellow"]
    BG_BLUE = _ANSI_BACKGROUND["blue"]
    BG_MAGENTA = _ANSI_BACKGROUND["magenta"]
    BG_CYAN = _ANSI_BACKGROUND["cyan"]
    BG_WHITE = _ANSI_BACKGROUND["white"]


@dataclass(frozen=True, slots=True)
class CursorPosition:
    """Cursor position in the terminal.
    
    Attributes:
        x: Horizontal position (column)
        y: Vertical position (row)
    """
    x: int = 0
    y: int = 0


@dataclass(frozen=True, slots=True)
class TerminalSize:
    """Terminal window dimensions.
    
    Attributes:
        width: Number of columns
        height: Number of rows
    """
    width: int = 80
    height: int = 24


class Cursor:
    """Cursor control utilities for terminal manipulation.
    
    Provides static methods for cursor positioning, visibility control,
    and screen clearing operations.
    
    Example:
        >>> output = Cursor.up(5) + "Moving up 5 lines"
        >>> print(output, end="")
    """
    
    @staticmethod
    def up(n: int = 1) -> str:
        """Move cursor up n lines.
        
        Args:
            n: Number of lines to move up
            
        Returns:
            ANSI escape sequence for cursor movement.
        """
        return f"\033[{n}A"
    
    @staticmethod
    def down(n: int = 1) -> str:
        """Move cursor down n lines.
        
        Args:
            n: Number of lines to move down
            
        Returns:
            ANSI escape sequence for cursor movement.
        """
        return f"\033[{n}B"
    
    @staticmethod
    def right(n: int = 1) -> str:
        """Move cursor right n columns.
        
        Args:
            n: Number of columns to move right
            
        Returns:
            ANSI escape sequence for cursor movement.
        """
        return f"\033[{n}C"
    
    @staticmethod
    def left(n: int = 1) -> str:
        """Move cursor left n columns.
        
        Args:
            n: Number of columns to move left
            
        Returns:
            ANSI escape sequence for cursor movement.
        """
        return f"\033[{n}D"
    
    @staticmethod
    def position(x: int, y: int) -> str:
        """Move cursor to specific position.
        
        Args:
            x: Column position (1-indexed)
            y: Row position (1-indexed)
            
        Returns:
            ANSI escape sequence for cursor positioning.
        """
        return f"\033[{y};{x}H"
    
    @staticmethod
    def hide() -> str:
        """Hide the cursor.
        
        Returns:
            ANSI escape sequence to hide cursor.
        """
        return "\033[?25l"
    
    @staticmethod
    def show() -> str:
        """Show the cursor.
        
        Returns:
            ANSI escape sequence to show cursor.
        """
        return "\033[?25h"
    
    @staticmethod
    def clear_screen() -> str:
        """Clear the entire screen.
        
        Returns:
            ANSI escape sequence to clear screen.
        """
        return "\033[2J"
    
    @staticmethod
    def clear_line() -> str:
        """Clear the current line.
        
        Returns:
            ANSI escape sequence to clear line.
        """
        return "\033[2K"
    
    @staticmethod
    def save() -> str:
        """Save cursor position.
        
        Returns:
            ANSI escape sequence to save cursor position.
        """
        return "\033[s"
    
    @staticmethod
    def restore() -> str:
        """Restore saved cursor position.
        
        Returns:
            ANSI escape sequence to restore cursor position.
        """
        return "\033[u"


class ProgressBar:
    """Progress bar renderer for terminal.
    
    Displays a visual progress indicator with optional percentage display.
    
    Attributes:
        current: Current progress value
    
    Example:
        >>> bar = ProgressBar(total=100, width=40)
        >>> print(bar.update(50))  # Shows 50% progress
    """
    
    def __init__(
        self,
        total: int = 100,
        width: int = 40,
        filled_char: str = "=",
        empty_char: str = "-",
        show_percentage: bool = True,
    ):
        self.total = total
        self.width = width
        self.filled_char = filled_char
        self.empty_char = empty_char
        self.show_percentage = show_percentage
        self.current = 0
    
    def update(self, current: int) -> str:
        """Update progress bar with new value.
        
        Args:
            current: Current progress value (clamped to total)
            
        Returns:
            Rendered progress bar string.
        """
        self.current = min(current, self.total)
        filled = int(self.width * self.current / self.total)
        empty = self.width - filled
        
        bar = self.filled_char * filled + self.empty_char * empty
        
        if self.show_percentage:
            pct = int(100 * self.current / self.total)
            return f"[{bar}] {pct}%"
        
        return f"[{bar}]"
    
    def render(self) -> str:
        """Render current progress state.
        
        Returns:
            Rendered progress bar string.
        """
        return self.update(self.current)


class TableRenderer:
    """Table renderer for terminal output.
    
    Renders ASCII tables with automatic column width calculation
    and optional width scaling for narrow terminals.
    
    Example:
        >>> renderer = TableRenderer(["Name", "Age"], [["Alice", "30"], ["Bob", "25"]])
        >>> print(renderer.render())
    """
    
    def __init__(
        self,
        headers: list[str],
        rows: Optional[list[list[str]]] = None,
        max_width: Optional[int] = None,
    ):
        self.headers = headers
        self.rows = rows or []
        self.max_width = max_width or TerminalSize().width
    
    def add_row(self, row: list[str]) -> None:
        """Add a row to the table.
        
        Args:
            row: List of cell values
        """
        self.rows.append(row)
    
    def render(self) -> str:
        """Render the table as a string.
        
        Returns:
            ASCII table string with borders.
        """
        col_widths = [len(h) for h in self.headers]
        
        for row in self.rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
        
        total_width = sum(col_widths) + len(self.headers) * 3 + 1
        if total_width > self.max_width:
            scale = self.max_width / total_width
            col_widths = [max(8, int(w * scale)) for w in col_widths]
        
        lines: list[str] = []
        
        separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
        lines.append(separator)
        
        header_line = "|" + "|".join(
            f" {h:<{col_widths[i]}} " for i, h in enumerate(self.headers)
        ) + "|"
        lines.append(header_line)
        lines.append(separator)
        
        for row in self.rows:
            row_line = "|" + "|".join(
                f" {str(row[i]):<{col_widths[i]}} " if i < len(row) else " " * (col_widths[i] + 2)
                for i in range(len(col_widths))
            ) + "|"
            lines.append(row_line)
        
        lines.append(separator)
        
        return "\n".join(lines)


class StatusIndicator:
    """Status indicator with icons and colors.
    
    Renders status messages with appropriate icons and colors
    for common states like success, error, warning, and info.
    
    Example:
        >>> print(StatusIndicator.render("success", "Operation completed"))
    """
    
    @classmethod
    def render(cls, status: str, message: str) -> str:
        """Render a status indicator.
        
        Args:
            status: Status type ("success", "error", "warning", "info", "loading", "pending")
            message: Message to display
            
        Returns:
            Colored status indicator string.
        """
        icon = _STATUS_ICONS.get(status, "•")
        color = _STATUS_COLORS.get(status, _ANSI_FOREGROUND["white"])
        
        return f"{color}{icon}{_ANSI_RESET} {message}"


class SpinnerAnimation:
    """Animated spinner for async operations.
    
    Displays a rotating spinner animation while an async operation
    is in progress.
    
    Example:
        >>> spinner = SpinnerAnimation("Loading data")
        >>> await spinner.start()
        >>> # ... do work ...
        >>> await spinner.stop()
    """
    
    def __init__(self, message: str = "Loading"):
        self.message = message
        self.frame = 0
        self.running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start the spinner animation."""
        import asyncio
        self.running = True
        self._task = asyncio.create_task(self._animate())
    
    async def stop(self) -> None:
        """Stop the spinner animation."""
        import asyncio
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        sys.stdout.write(Cursor.left(50) + " " * 50 + Cursor.left(50))
        sys.stdout.flush()
    
    async def _animate(self) -> None:
        """Run the spinner animation."""
        while self.running:
            frame = _SPINNER_FRAMES[self.frame % len(_SPINNER_FRAMES)]
            sys.stdout.write(f"\r{frame} {self.message}...")
            sys.stdout.flush()
            await asyncio.sleep(0.1)
            self.frame += 1


class KeybindingHint:
    """Keyboard shortcut hint renderer.
    
    Formats keyboard shortcuts for display in the terminal.
    
    Example:
        >>> print(KeybindingHint.render("Ctrl+C", "Copy selection"))
    """
    
    @staticmethod
    def render(keys: str, description: str) -> str:
        """Render a keybinding hint.
        
        Args:
            keys: Key combination string
            description: Description of the action
            
        Returns:
            Formatted keybinding hint string.
        """
        key_str = f"[{_ANSI_BOLD}{keys}{_ANSI_RESET}]"
        return f"{key_str} {description}"
    
    @staticmethod
    def format_shortcut(keys: list[str]) -> str:
        """Format a keyboard shortcut.
        
        Args:
            keys: List of keys in the shortcut
            
        Returns:
            Formatted shortcut string with bold styling.
        """
        return "+".join(
            _ANSI_BOLD + k.upper() + _ANSI_RESET
            for k in keys
        )


class DiffRenderer:
    """Diff rendering for terminal.
    
    Provides colored diff output for comparing text changes
    using the unified diff format.
    
    Example:
        >>> old = ["def foo():", "    pass"]
        >>> new = ["def foo():", "    return 1"]
        >>> print(DiffRenderer.render_diff(old, new))
    """
    
    @staticmethod
    def render_diff(
        old_lines: list[str],
        new_lines: list[str],
        context: int = 3,
    ) -> str:
        """Render diff between two sets of lines.
        
        Args:
            old_lines: Original lines
            new_lines: Modified lines
            context: Number of context lines to show
            
        Returns:
            Colored diff string.
        """
        from difflib import unified_diff
        
        diff = list(unified_diff(
            old_lines,
            new_lines,
            lineterm="",
            n=context,
        ))
        
        lines: list[str] = []
        for line in diff:
            if line.startswith("+++") or line.startswith("---"):
                lines.append(f"{_ANSI_DIM}{line}{_ANSI_RESET}")
            elif line.startswith("+"):
                lines.append(f"{_ANSI_FOREGROUND['green']}{line}{_ANSI_RESET}")
            elif line.startswith("-"):
                lines.append(f"{_ANSI_FOREGROUND['red']}{line}{_ANSI_RESET}")
            elif line.startswith("@@"):
                lines.append(f"{_ANSI_FOREGROUND['cyan']}{line}{_ANSI_RESET}")
            else:
                lines.append(line)
        
        return "\n".join(lines)


class MarkdownRenderer:
    """Basic markdown rendering for terminal.
    
    Converts markdown text to terminal-friendly output with
    basic styling for headers, lists, and code blocks.
    
    Example:
        >>> md = "# Hello\n- Item 1\n- Item 2"
        >>> print(MarkdownRenderer.render(md))
    """
    
    @staticmethod
    def render(text: str) -> str:
        """Render markdown to terminal.
        
        Args:
            text: Markdown text to render
            
        Returns:
            Terminal-formatted string.
        """
        lines = text.split("\n")
        output: list[str] = []
        
        in_code_block = False
        in_list = False
        
        for line in lines:
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            
            if in_code_block:
                output.append(line)
                continue
            
            if line.strip().startswith("# "):
                output.append(f"{_ANSI_BOLD}{line[2:]}{_ANSI_RESET}")
            elif line.strip().startswith("## "):
                output.append(f"{_ANSI_BOLD}{line[3:]}{_ANSI_RESET}")
            elif line.strip().startswith("### "):
                output.append(f"{_ANSI_BOLD}{line[4:]}{_ANSI_RESET}")
            elif line.strip().startswith("- ") or line.strip().startswith("* "):
                if not in_list:
                    output.append("")
                    in_list = True
                output.append(f"  • {line[2:]}")
            elif line.strip().isdigit() and line.strip() + "." in line:
                if not in_list:
                    output.append("")
                    in_list = True
                output.append(f"  {line}")
            else:
                in_list = False
                output.append(line)
        
        return "\n".join(output)


class ToolResultRenderer:
    """Tool result rendering with rich formatting.
    
    Provides formatted output for tool execution results
    with status indicators and optional truncation.
    """
    
    @staticmethod
    def render(
        tool_name: str,
        result: Any,
        success: bool = True,
        truncate: int = 1000,
    ) -> str:
        """Render tool result.
        
        Args:
            tool_name: Name of the tool that was executed
            result: Result from the tool execution
            success: Whether the tool executed successfully
            truncate: Maximum length of result string
            
        Returns:
            Formatted tool result string.
        """
        status = StatusIndicator.render(
            "success" if success else "error",
            f"Tool: {tool_name}",
        )
        
        result_str = str(result)
        if len(result_str) > truncate:
            result_str = result_str[:truncate] + "..."
        
        return f"{status}\n{result_str}"


class ToolSelector:
    """Tool selector UI component.
    
    Interactive tool selection UI for navigating and
    selecting from a list of available tools.
    
    Attributes:
        selected: Index of currently selected tool
    """
    
    def __init__(self, tools: list[dict[str, str]]):
        self._tools = tools
        self._selected = 0
    
    @property
    def selected(self) -> int:
        """Get the currently selected index."""
        return self._selected
    
    @selected.setter
    def selected(self, value: int) -> None:
        """Set the selected index."""
        self._selected = value
    
    def render(self, max_display: int = 10) -> str:
        """Render tool selector.
        
        Args:
            max_display: Maximum number of tools to display
            
        Returns:
            Rendered tool selector string.
        """
        lines: list[str] = []
        
        start_idx = max(0, self._selected - max_display + 1)
        end_idx = min(len(self._tools), start_idx + max_display)
        
        for i in range(start_idx, end_idx):
            tool = self._tools[i]
            prefix = "› " if i == self._selected else "  "
            
            if i == self._selected:
                line = f"{_ANSI_BOLD}{prefix}{tool.get('name', 'unknown')}{_ANSI_RESET}"
                if tool.get("description"):
                    line += f"\n    {tool['description']}"
            else:
                line = f"{prefix}{tool.get('name', 'unknown')}"
            
            lines.append(line)
        
        if len(self._tools) > max_display:
            lines.append(f"  ... and {len(self._tools) - max_display} more")
        
        return "\n".join(lines)
    
    def select_next(self) -> None:
        """Select the next tool."""
        self._selected = (self._selected + 1) % len(self._tools)
    
    def select_prev(self) -> None:
        """Select the previous tool."""
        self._selected = (self._selected - 1) % len(self._tools)
    
    def get_selected(self) -> Optional[dict[str, str]]:
        """Get the currently selected tool.
        
        Returns:
            Tool dictionary or None if no tools available.
        """
        if 0 <= self._selected < len(self._tools):
            return self._tools[self._selected]
        return None


class ContextVisualization:
    """Context visualization for tokens and files.
    
    Provides visual representation of context usage including
    token count and files read.
    """
    
    @staticmethod
    def render_context_bar(
        tokens_used: int,
        token_limit: int,
        files_read: int,
    ) -> str:
        """Render context usage bar.
        
        Args:
            tokens_used: Current token usage
            token_limit: Maximum token limit
            files_read: Number of files read
            
        Returns:
            Formatted context bar string with color coding.
        """
        token_pct = min(100, int(100 * tokens_used / token_limit))
        
        bar_width = 30
        filled = int(bar_width * tokens_used / token_limit)
        bar = "█" * filled + "░" * (bar_width - filled)
        
        color = _ANSI_FOREGROUND["green"]
        if token_pct > 70:
            color = _ANSI_FOREGROUND["yellow"]
        if token_pct > 90:
            color = _ANSI_FOREGROUND["red"]
        
        return (
            f"Context: [{color}{bar}{_ANSI_RESET}] "
            f"{token_pct}% ({tokens_used}/{token_limit}) | "
            f"Files: {files_read}"
        )


__all__ = [
    "AnsiCode",
    "CursorPosition",
    "TerminalSize",
    "Cursor",
    "ProgressBar",
    "TableRenderer",
    "StatusIndicator",
    "SpinnerAnimation",
    "KeybindingHint",
    "DiffRenderer",
    "MarkdownRenderer",
    "ToolResultRenderer",
    "ToolSelector",
    "ContextVisualization",
]

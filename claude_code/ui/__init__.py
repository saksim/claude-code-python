"""
UI components for Claude Code Python.

Provides console-based UI components using the Rich library.
"""

from claude_code.ui.console import (
    ConsoleUI,
    RichConsole,
    get_console,
)

from claude_code.ui.messages import (
    MessageFormatter,
    format_user_message,
    format_assistant_message,
    format_system_message,
    format_tool_result,
)

from claude_code.ui.panels import (
    Panel,
    CollapsiblePanel,
    InfoPanel,
    WarningPanel,
    ErrorPanel,
)

from claude_code.ui.tables import (
    create_table,
    format_key_value_table,
)

from claude_code.ui.spinner import (
    Spinner,
    ProgressSpinner,
)

from claude_code.ui.rendering import (
    AnsiCode,
    Cursor,
    ProgressBar,
    TableRenderer,
    StatusIndicator,
    SpinnerAnimation,
    KeybindingHint,
    DiffRenderer,
    MarkdownRenderer,
    ToolResultRenderer,
    ToolSelector,
    ContextVisualization,
)

__all__ = [
    # Console
    "ConsoleUI",
    "RichConsole",
    "get_console",
    
    # Messages
    "MessageFormatter",
    "format_user_message",
    "format_assistant_message",
    "format_system_message",
    "format_tool_result",
    
    # Panels
    "Panel",
    "CollapsiblePanel",
    "InfoPanel",
    "WarningPanel",
    "ErrorPanel",
    
    # Tables
    "create_table",
    "format_key_value_table",
    
    # Spinners
    "Spinner",
    "ProgressSpinner",
    
    # Rendering
    "AnsiCode",
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

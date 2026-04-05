"""Console UI for Claude Code Python.

Provides console output functionality using Rich.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

try:
    from rich.box import ROUNDED, Box
    from rich.console import Console as RichConsoleClass
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.style import Style
    from rich.syntax import Syntax
    from rich.table import Table

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    RichConsoleClass = None
    Panel = None
    Table = None
    Syntax = None
    Markdown = None
    ROUNDED = None
    Box = None
    Style = None


@dataclass(frozen=True, slots=True)
class ConsoleConfig:
    """Console configuration.

    Attributes:
        width: Console width in characters.
        height: Console height in lines.
        force_terminal: Force terminal output.
        no_color: Disable colors.
        show_line_numbers: Show line numbers in code.
    """

    width: int | None = None
    height: int | None = None
    force_terminal: bool = True
    no_color: bool = False
    show_line_numbers: bool = False


class RichConsole:
    """Rich console wrapper for styled output.

    Provides consistent styling for all CLI output.
    """

    def __init__(self, config: ConsoleConfig | None = None) -> None:
        """Initialize RichConsole.

        Args:
            config: Console configuration.
        """
        self._config = config or ConsoleConfig()

        if RICH_AVAILABLE:
            self._console = RichConsoleClass(
                width=self._config.width,
                height=self._config.height,
                force_terminal=self._config.force_terminal,
                no_color=self._config.no_color,
            )
        else:
            self._console = None

    def print(self, *args: Any, **kwargs: Any) -> None:
        """Print to console.

        Args:
            *args: Positional arguments for print.
            **kwargs: Keyword arguments for print.
        """
        if self._console:
            self._console.print(*args, **kwargs)
        else:
            print(*args)

    def print_markdown(self, text: str) -> None:
        """Print markdown text.

        Args:
            text: Markdown text to print.
        """
        if self._console and Markdown:
            md = Markdown(text)
            self._console.print(md)
        else:
            print(text)

    def print_panel(
        self,
        content: str,
        title: str | None = None,
        border_style: str = "blue",
        box: Box | None = None,
    ) -> None:
        """Print content in a panel.

        Args:
            content: Content to display.
            title: Panel title.
            border_style: Border color/style.
            box: Box style for panel border.
        """
        if self._console and Panel:
            panel = Panel(
                content,
                title=title,
                border_style=border_style,
                box=box or ROUNDED,
            )
            self._console.print(panel)
        else:
            if title:
                print(f"=== {title} ===")
            print(content)

    def print_table(
        self,
        headers: list[str],
        rows: list[list[str]],
        title: str | None = None,
    ) -> None:
        """Print a table.

        Args:
            headers: Column headers.
            rows: Table rows.
            title: Table title.
        """
        if self._console and Table:
            table = Table(title=title, show_header=True)
            for header in headers:
                table.add_column(header)
            for row in rows:
                table.add_row(*[str(c) for c in row])
            self._console.print(table)
        else:
            if title:
                print(f"=== {title} ===")
            header_line = " | ".join(headers)
            print(header_line)
            print("-" * len(header_line))
            for row in rows:
                print(" | ".join(str(c) for c in row))

    def print_syntax(
        self,
        code: str,
        language: str = "python",
        line_numbers: bool = False,
    ) -> None:
        """Print syntax-highlighted code.

        Args:
            code: Code to highlight.
            language: Programming language.
            line_numbers: Whether to show line numbers.
        """
        if self._console and Syntax:
            syntax = Syntax(
                code,
                language,
                line_numbers=line_numbers or self._config.show_line_numbers,
            )
            self._console.print(syntax)
        else:
            print(code)

    def clear(self) -> None:
        """Clear the console."""
        if self._console:
            self._console.clear()
        else:
            print("\033[2J\033[H")

    def rule(self, title: str | None = None) -> None:
        """Print a horizontal rule.

        Args:
            title: Optional title for the rule.
        """
        if self._console:
            self._console.rule(title)
        else:
            print("=" * 60)


class ConsoleUI:
    """Main console UI class.

    Provides high-level UI methods for the CLI.
    """

    def __init__(self, console: RichConsole | None = None) -> None:
        """Initialize ConsoleUI.

        Args:
            console: RichConsole instance to use.
        """
        self._console = console or RichConsole()

    @property
    def console(self) -> RichConsole:
        """Get the console instance."""
        return self._console

    def show_welcome(self) -> None:
        """Show welcome message."""
        welcome = """
# Claude Code Python

A Python implementation of an AI programming assistant.

Type your message or use `/help` for available commands.
        """
        self._console.print_markdown(welcome)

    def show_message(self, role: str, content: str) -> None:
        """Show a message.

        Args:
            role: Message role (user/assistant/system).
            content: Message content.
        """
        if role == "user":
            self._console.print_panel(
                f"[bold cyan]You:[/bold cyan]\n{content}",
                border_style="cyan",
            )
        elif role == "assistant":
            self._console.print_panel(
                content,
                title="Claude",
                border_style="green",
            )
        elif role == "system":
            self._console.print_panel(
                content,
                title="System",
                border_style="yellow",
            )

    def show_error(self, message: str) -> None:
        """Show an error message.

        Args:
            message: Error message to display.
        """
        if self._console._console and Panel:
            panel = Panel(
                f"[bold red]Error:[/bold red] {message}",
                border_style="red",
            )
            self._console._console.print(panel)
        else:
            print(f"ERROR: {message}")

    def show_success(self, message: str) -> None:
        """Show a success message.

        Args:
            message: Success message to display.
        """
        if self._console._console and Panel:
            panel = Panel(
                f"[bold green]Success:[/bold green] {message}",
                border_style="green",
            )
            self._console._console.print(panel)
        else:
            print(f"SUCCESS: {message}")

    def show_info(self, message: str) -> None:
        """Show an info message.

        Args:
            message: Info message to display.
        """
        if self._console._console and Panel:
            panel = Panel(
                f"[bold blue]Info:[/bold blue] {message}",
                border_style="blue",
            )
            self._console._console.print(panel)
        else:
            print(f"INFO: {message}")

    def show_tool_result(
        self,
        tool_name: str,
        result: str,
        success: bool = True,
    ) -> None:
        """Show a tool result.

        Args:
            tool_name: Name of the tool.
            result: Tool result content.
            success: Whether the tool succeeded.
        """
        border = "green" if success else "red"
        self._console.print_panel(
            result,
            title=f"Tool: {tool_name}",
            border_style=border,
        )

    def show_help(self, help_text: str) -> None:
        """Show help text.

        Args:
            help_text: Help text to display.
        """
        self._console.print_markdown(help_text)

    def show_stats(self, stats: dict[str, Any]) -> None:
        """Show statistics.

        Args:
            stats: Statistics dictionary to display.
        """
        rows = [[k, str(v)] for k, v in stats.items()]
        self._console.print_table(
            ["Metric", "Value"],
            rows,
            title="Session Statistics",
        )


_console: RichConsole | None = None


def get_console() -> RichConsole:
    """Get the global console instance.

    Returns:
        Global RichConsole instance.
    """
    global _console
    if _console is None:
        _console = RichConsole()
    return _console


def get_ui() -> ConsoleUI:
    """Get the global UI instance.

    Returns:
        Global ConsoleUI instance.
    """
    return ConsoleUI(get_console())
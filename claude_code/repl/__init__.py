"""REPL Interface for Claude Code Python.

Interactive command-line interface for Claude Code.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Dataclass patterns
- Rich terminal UI
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from dataclasses import dataclass
from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from claude_code.commands.registry import get_all_commands


@dataclass(frozen=True, slots=True)
class REPLConfig:
    """Configuration for the REPL.

    Attributes:
        working_directory: Current working directory.
        verbose: Enable verbose output.
        stream_output: Stream output to console.
        show_timing: Show timing information.
        welcome_message: Show welcome message on startup.
    """

    working_directory: str = ""
    verbose: bool = False
    stream_output: bool = True
    show_timing: bool = True
    welcome_message: bool = True


class REPL:
    """Interactive REPL for Claude Code.

    Provides a rich terminal interface for interacting with Claude.
    Supports:
    - Interactive command input
    - Markdown rendering
    - Command history
    - Slash commands (/help, /clear, /model, etc.)
    """

    def __init__(
        self,
        engine: Any,
        config: REPLConfig | None = None,
    ) -> None:
        """Initialize REPL.

        Args:
            engine: Query engine for processing input.
            config: REPL configuration.
        """
        self._engine = engine
        self._config = config or REPLConfig()
        if not self._config.working_directory:
            self._config.working_directory = os.getcwd()
        self._console = Console()
        self._history: list[tuple[str, str]] = []
        self._running = False
        self._commands = get_all_commands()

    @property
    def config(self) -> REPLConfig:
        """Get REPL configuration."""
        return self._config

    @property
    def engine(self) -> Any:
        """Get the query engine."""
        return self._engine

    @property
    def console(self) -> Console:
        """Get the Rich console."""
        return self._console

    def print_welcome(self) -> None:
        """Print welcome message."""
        if not self._config.welcome_message:
            return

        welcome = """
# Claude Code Python

A Python implementation of an AI programming assistant.

**Available Commands:**
- `/help` - Show this help message
- `/clear` - Clear conversation history
- `/model <name>` - Switch model
- `/cost` - Show session cost
- `/exit` or `/quit` - Exit Claude Code

**Tips:**
- Claude will use tools to help you with coding tasks
- Type your question or task and press Enter
- Use Ctrl+C to interrupt the current operation
        """
        self._console.print(Markdown(welcome))

    def print_error(self, message: str) -> None:
        """Print error message.

        Args:
            message: Error message to display.
        """
        self._console.print(
            Panel(
                f"[bold red]Error:[/bold red] {message}",
                title="Error",
                border_style="red",
            )
        )

    def print_success(self, message: str) -> None:
        """Print success message.

        Args:
            message: Success message to display.
        """
        self._console.print(
            Panel(
                f"[bold green]Success:[/bold green] {message}",
                title="Success",
                border_style="green",
            )
        )

    def print_info(self, message: str) -> None:
        """Print info message.

        Args:
            message: Info message to display.
        """
        self._console.print(Panel(message, border_style="blue"))

    def format_response(self, content: str) -> str:
        """Format response content for display.

        Args:
            content: Raw response content.

        Returns:
            Formatted content with ANSI codes removed.
        """
        return re.sub(r"\x1b\[[0-9;]*m", "", content)

    def display_message(self, role: str, content: str) -> None:
        """Display a message in the chat.

        Args:
            role: Message role (user/assistant).
            content: Message content.
        """
        if role == "assistant":
            try:
                md = Markdown(content)
                self._console.print(md)
            except Exception:
                self._console.print(content)
        else:
            self._console.print(f"[dim]{role}:[/dim] {content}")

    def display_tool_use(self, tool_name: str, input_data: dict[str, Any]) -> None:
        """Display a tool use.

        Args:
            tool_name: Name of the tool.
            input_data: Input data for the tool.
        """
        tool_display = f"[bold cyan]Using tool:[/bold cyan] {tool_name}"
        input_str = json.dumps(input_data, indent=2)[:500] if input_data else ""

        self._console.print(
            Panel(
                f"{tool_display}\n\n[dim]Input:[/dim]\n{input_str}",
                border_style="cyan",
            )
        )

    def display_tool_result(self, result: str, is_error: bool = False) -> None:
        """Display a tool result.

        Args:
            result: Tool result content.
            is_error: Whether the result is an error.
        """
        style = "red" if is_error else "green"
        border = "red" if is_error else "green"
        display_result = result[:2000] + "\n... (truncated)" if len(result) > 2000 else result

        self._console.print(
            Panel(
                f"[{style}]{display_result}[/{style}]",
                title="Tool Result",
                border_style=border,
            )
        )

    async def run_command(self, command: str) -> bool:
        """Process a slash command.

        Args:
            command: The command string (e.g., "/help").

        Returns:
            True if command was handled, False otherwise.
        """
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        handler = self._commands.get(cmd)
        if handler:
            return await handler.execute(self, args)

        if cmd.startswith("/"):
            self.print_error(f"Unknown command: {cmd}")
            return True

        return False

    async def run(self) -> None:
        """Run the REPL loop."""
        self._running = True
        self.print_welcome()

        while self._running:
            try:
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: Prompt.ask("\n[bold blue]You[/bold blue]"),
                )

                if not user_input.strip():
                    continue

                self._history.append(("user", user_input))

                if user_input.strip().startswith("/"):
                    if await self.run_command(user_input):
                        continue

                self._console.print()
                start_time = asyncio.get_event_loop().time()

                try:
                    async for event in self._engine.query(user_input):
                        await self._handle_event(event)

                    if self._config.show_timing:
                        elapsed = asyncio.get_event_loop().time() - start_time
                        self._console.print(f"\n[dim]Completed in {elapsed:.2f}s[/dim]")

                except KeyboardInterrupt:
                    self._engine.interrupt()
                    self._console.print("\n[yellow]Interrupted[/yellow]")

            except EOFError:
                break
            except Exception as e:
                self.print_error(str(e))

        self._console.print("[dim]Session ended[/dim]")

    async def _handle_event(self, event: Any) -> None:
        """Handle an event from the query engine.

        Args:
            event: Event from the query engine.
        """
        if isinstance(event, dict):
            event_type = event.get("type")

            if event_type == "text":
                text = event.get("content", "")
                self._console.print(self.format_response(text), end="")

            elif event_type == "stop_reason":
                reason = event.get("reason", "unknown")
                if self._config.verbose:
                    self._console.print(f"\n[dim]Stopped: {reason}[/dim]")

            elif event_type == "error":
                self.print_error(event.get("error", "Unknown error"))

        elif hasattr(event, "role"):
            if event.role == "assistant":
                content = event.content
                if isinstance(content, str):
                    self._console.print(Markdown(content))

        elif hasattr(event, "name"):
            self.display_tool_use(event.name, getattr(event, "input", {}))

        elif hasattr(event, "result"):
            result = event.result
            self.display_tool_result(
                getattr(result, "content", str(result)),
                getattr(result, "is_error", False),
            )


class PipeMode:
    """Non-interactive pipe mode for single queries."""

    def __init__(self, engine: Any) -> None:
        """Initialize PipeMode.

        Args:
            engine: Query engine for processing input.
        """
        self._engine = engine

    async def run(self) -> int:
        """Run in pipe mode.

        Returns:
            Exit code (0 for success, 1 for error).
        """
        try:
            user_input = sys.stdin.read()

            if not user_input.strip():
                return 0

            response_parts = []

            async for event in self._engine.query(user_input):
                if isinstance(event, dict) and event.get("type") == "text":
                    response_parts.append(event.get("content", ""))
                elif hasattr(event, "content"):
                    response_parts.append(str(event.content))

            sys.stdout.write("".join(response_parts))
            sys.stdout.flush()

            return 0

        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")
            return 1


__all__ = [
    "REPL",
    "REPLConfig",
    "PipeMode",
]
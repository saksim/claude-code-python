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

from claude_code.commands.base import CommandContext, CommandResult
from claude_code.commands.registry import get_all_commands
from claude_code.services.hooks_manager import HookEvent


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

    def _extract_text_content(self, content: Any) -> str:
        """Extract plain text from assistant content blocks."""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(str(block.get("text", "")))
            return "".join(parts)
        return str(content)

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
        raw_cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        cmd = raw_cmd[1:] if raw_cmd.startswith("/") else raw_cmd

        handler = self._resolve_command_handler(cmd)
        if handler:
            context = self._build_command_context()
            await self._trigger_command_hook(
                HookEvent.BEFORE_COMMAND,
                self._build_command_hook_context(
                    command_name=cmd,
                    command_args=args,
                    phase=HookEvent.BEFORE_COMMAND.value,
                ),
            )
            try:
                result = await handler.execute(args, context)
            except Exception as exc:
                error_message = f"Command '/{cmd}' failed: {exc}"
                await self._trigger_command_hook(
                    HookEvent.ON_ERROR,
                    self._build_command_hook_context(
                        command_name=cmd,
                        command_args=args,
                        phase=HookEvent.ON_ERROR.value,
                        error=error_message,
                    ),
                )
                self.print_error(error_message)
                return True

            await self._trigger_command_hook(
                HookEvent.AFTER_COMMAND,
                self._build_command_hook_context(
                    command_name=cmd,
                    command_args=args,
                    phase=HookEvent.AFTER_COMMAND.value,
                    result=result,
                ),
            )
            if not result.success:
                await self._trigger_command_hook(
                    HookEvent.ON_ERROR,
                    self._build_command_hook_context(
                        command_name=cmd,
                        command_args=args,
                        phase=HookEvent.ON_ERROR.value,
                        result=result,
                        error=result.error or "Command failed",
                    ),
                )
            self._render_command_result(result)
            return True

        if raw_cmd.startswith("/"):
            await self._trigger_command_hook(
                HookEvent.ON_ERROR,
                self._build_command_hook_context(
                    command_name=cmd,
                    command_args=args,
                    phase=HookEvent.ON_ERROR.value,
                    error=f"Unknown command: /{cmd}",
                ),
            )
            self.print_error(f"Unknown command: /{cmd}")
            return True

        return False

    def _resolve_command_handler(self, name: str) -> Any | None:
        """Resolve command handler by name or alias."""
        handler = self._commands.get(name)
        if handler is not None:
            return handler

        for candidate in self._commands.values():
            if name in getattr(candidate, "aliases", []):
                return candidate
        return None

    def _build_command_context(self) -> CommandContext:
        """Build command execution context from current runtime state."""
        return CommandContext(
            working_directory=self._config.working_directory,
            console=self._console,
            engine=self._engine,
            session=self._build_session_payload(),
            config=getattr(self._engine, "config", None),
        )

    def _build_session_payload(self) -> dict[str, Any] | None:
        """Build session metadata payload for command compatibility."""
        session_manager = getattr(self._engine, "session_manager", None)
        if session_manager is not None and hasattr(session_manager, "get_current_session"):
            current = session_manager.get_current_session()
            if current is not None and hasattr(current, "metadata"):
                metadata = current.metadata
                return {
                    "id": metadata.id,
                    "created_at": metadata.created_at,
                    "last_active": metadata.last_active,
                    "working_directory": metadata.working_directory,
                    "message_count": metadata.message_count,
                    "tool_call_count": metadata.tool_call_count,
                }

        engine_config = getattr(self._engine, "config", None)
        session_id = getattr(engine_config, "session_id", None)
        if session_id is None:
            return None

        return {
            "id": session_id,
            "message_count": len(getattr(self._engine, "messages", [])),
            "tool_call_count": len(getattr(self._engine, "tool_results", [])),
        }

    def _render_command_result(self, result: CommandResult) -> None:
        """Render command execution result to console."""
        if result is None:
            return
        if not result.success:
            self.print_error(result.error or "Command failed")
            return
        if result.is_silent:
            return
        if result.content:
            content = str(result.content)
            try:
                self._console.print(Markdown(content))
            except Exception:
                self._console.print(content)

    def _get_hooks_manager(self) -> Any | None:
        """Resolve hooks manager from runtime engine."""
        manager = getattr(self._engine, "hooks_manager", None)
        if manager is None or not hasattr(manager, "trigger"):
            return None
        return manager

    def _build_command_hook_context(
        self,
        *,
        command_name: str,
        command_args: str,
        phase: str,
        result: CommandResult | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        """Build normalized command hook context payload."""
        engine_config = getattr(self._engine, "config", None)
        context: dict[str, Any] = {
            "source": "repl",
            "phase": phase,
            "command_name": command_name,
            "command_args": command_args,
            "working_directory": self._config.working_directory,
            "session_id": getattr(engine_config, "session_id", None),
            "model": getattr(engine_config, "model", None),
        }
        if result is not None:
            context["success"] = result.success
            if result.content is not None:
                context["result_content"] = str(result.content)
            if result.error:
                context["result_error"] = result.error
        if error:
            context["error"] = error
        return context

    async def _trigger_command_hook(
        self,
        event: HookEvent,
        context: dict[str, Any],
    ) -> None:
        """Trigger command hook event when hooks manager is available."""
        manager = self._get_hooks_manager()
        if manager is None:
            return
        try:
            await manager.trigger(event, context)
        except Exception:
            return

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
                content = self._extract_text_content(event.content)
                if content:
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
                    content = event.content
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                response_parts.append(str(block.get("text", "")))
                    else:
                        response_parts.append(str(content))

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

"""
Claude Code Python - Main Entry Point
CLI interface and initialization.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Async/await patterns
- Environment variable support
- Multiple execution modes
"""

from __future__ import annotations

import os
import sys
import asyncio
import argparse
import io
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any

from claude_code.api.client import APIClient, APIClientConfig, APIProvider
from claude_code.engine.query import QueryEngine, QueryConfig
from claude_code.engine.context import ContextBuilder
from claude_code.engine.session import SessionManager, SQLiteSessionStore
from claude_code.repl import REPL, REPLConfig, PipeMode
from claude_code.tools.registry import create_default_registry
from claude_code.tasks.factory import TaskBackendConfig, create_task_manager_with_event_journal
from claude_code.tasks.manager import TaskManager
from claude_code.services.event_journal import EventJournal, SQLiteEventJournal
from claude_code.services.hooks_manager import HooksManager
from claude_code.services.history_manager import HistoryManager
from claude_code.services.memory_service import SessionMemory, get_memory
from claude_code.commands.registry import setup_default_commands
from claude_code.config import Config, get_config
from claude_code.app import Application, AppConfig


@dataclass(frozen=True, slots=True)
class RuntimeContext:
    """Runtime bootstrap result shared by all execution modes."""

    application: Application
    app_config: Config
    api_client: APIClient
    tool_registry: Any
    query_engine: QueryEngine
    session_manager: SessionManager
    history_manager: HistoryManager
    task_manager: TaskManager
    hooks_manager: HooksManager
    memory: SessionMemory
    event_journal: EventJournal | SQLiteEventJournal
    working_directory: str


@dataclass(frozen=True, slots=True)
class DaemonClientMode:
    """Resolved daemon thin-client mode for CLI query paths."""

    enabled: bool
    base_url: str
    timeout_seconds: float
    required: bool


def _resolve_memory_scope(raw_scope: str | None) -> str:
    """Resolve runtime memory scope with safe fallback."""
    candidate = (raw_scope or "").strip().lower()
    if candidate in {"user", "project", "local"}:
        return candidate
    return "project"


@dataclass(frozen=True, slots=True)
class InterpreterDiagnostics:
    """Interpreter source diagnostics for doctor output."""

    executable: str
    python_on_path: Optional[str]
    executable_source: str
    python_on_path_source: str
    has_windowsapps_stub_risk: bool
    warning: Optional[str]
    recommended_launcher: str


def _resolve_path_for_diagnostics(path: Optional[str]) -> Optional[str]:
    """Resolve path for diagnostics output without requiring file existence."""
    if not path:
        return None
    try:
        return str(Path(path).expanduser().resolve(strict=False))
    except Exception:
        return str(path)


def _classify_interpreter_path(path: Optional[str], platform_name: Optional[str] = None) -> str:
    """Classify interpreter source by path pattern."""
    if not path:
        return "unknown"

    platform_value = platform_name or sys.platform
    lower = path.replace("/", "\\").lower()

    if platform_value == "win32":
        if "\\appdata\\local\\microsoft\\windowsapps\\python" in lower:
            return "windowsapps_stub"
        if "\\anaconda" in lower or "\\miniconda" in lower or "\\conda\\" in lower:
            return "conda"
        if "\\.venv\\" in lower or "\\venv\\" in lower:
            return "virtualenv"
        return "system"

    posix_lower = path.replace("\\", "/").lower()
    if "/.venv/" in posix_lower or "/venv/" in posix_lower:
        return "virtualenv"
    if "/anaconda" in posix_lower or "/miniconda" in posix_lower or "/conda/" in posix_lower:
        return "conda"
    return "system"


def _is_windowsapps_stub(path: Optional[str], platform_name: Optional[str] = None) -> bool:
    """Return True when path resolves to WindowsApps Python alias stub."""
    platform_value = platform_name or sys.platform
    if platform_value != "win32":
        return False
    return _classify_interpreter_path(path, platform_name=platform_value) == "windowsapps_stub"


def _collect_interpreter_diagnostics(
    *,
    platform_name: Optional[str] = None,
    executable_path: Optional[str] = None,
    python_on_path: Optional[str] = None,
) -> InterpreterDiagnostics:
    """Collect interpreter diagnostics for doctor and runtime troubleshooting."""
    platform_value = platform_name or sys.platform
    resolved_executable = _resolve_path_for_diagnostics(executable_path or sys.executable) or "N/A"
    resolved_python_on_path = _resolve_path_for_diagnostics(
        python_on_path if python_on_path is not None else shutil.which("python")
    )

    executable_source = _classify_interpreter_path(resolved_executable, platform_name=platform_value)
    python_on_path_source = _classify_interpreter_path(
        resolved_python_on_path,
        platform_name=platform_value,
    )

    warning: Optional[str] = None
    if platform_value == "win32":
        risky_locations: list[str] = []
        if _is_windowsapps_stub(resolved_executable, platform_name=platform_value):
            risky_locations.append("sys.executable")
        if _is_windowsapps_stub(resolved_python_on_path, platform_name=platform_value):
            risky_locations.append("python on PATH")
        if risky_locations:
            warning = (
                "WindowsApps python.exe stub detected in "
                + " + ".join(risky_locations)
                + ". Use a real interpreter instead of Microsoft Store alias."
            )

    has_risk = warning is not None
    if platform_value == "win32":
        if has_risk:
            recommended_launcher = (
                "Use `py -3 -m claude_code.main` or `<venv>\\Scripts\\python -m claude_code.main`; "
                "disable App execution aliases for python/python3 if needed."
            )
        else:
            recommended_launcher = (
                "Use `py -3 -m claude_code.main` (preferred) or "
                "`<venv>\\Scripts\\python -m claude_code.main`."
            )
    else:
        recommended_launcher = "Use `python -m claude_code.main` from the project virtualenv."

    return InterpreterDiagnostics(
        executable=resolved_executable,
        python_on_path=resolved_python_on_path,
        executable_source=executable_source,
        python_on_path_source=python_on_path_source,
        has_windowsapps_stub_risk=has_risk,
        warning=warning,
        recommended_launcher=recommended_launcher,
    )


def _configure_windows_console_encoding() -> None:
    """Configure UTF-8 console streams on Windows for CLI execution.
    
    This is intentionally invoked from ``main()`` instead of module import
    to avoid side-effects in test runners and library imports.
    """
    if sys.platform != "win32":
        return
    
    if hasattr(sys.stdout, "buffer"):
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "buffer"):
        try:
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
        except Exception:
            pass


def setup_api_client(app_config: Optional[Config] = None) -> APIClient:
    """Setup the API client based on environment.
    
    Resolution order:
    1) Environment variables
    2) Loaded config values
    
    Returns:
        Configured APIClient instance.
        
    Raises:
        ValueError: If required environment variables are missing.
    """
    if app_config is None:
        app_config = get_config()

    # Check for API provider
    provider = os.getenv("CLAUDE_API_PROVIDER", app_config.api_provider).lower()
    
    # Build config based on provider
    if provider == "anthropic":
        config_api_key = app_config.api_key if app_config.api_provider == "anthropic" else None
        api_key = os.getenv("ANTHROPIC_API_KEY") or config_api_key
        config = APIClientConfig(
            provider=APIProvider.ANTHROPIC,
            api_key=api_key,
        )
    elif provider in ("openai", "ollama", "vllm", "deepseek"):
        default_urls = {
            "ollama": "http://localhost:11434/v1",
            "vllm": "http://localhost:8000/v1",
            "deepseek": "https://api.deepseek.com/v1",
        }
        base_url = (
            os.getenv("OPENAI_BASE_URL")
            or app_config.openai_base_url
            or default_urls.get(provider)
        )
        config_api_key = (
            app_config.api_key
            if app_config.api_provider in ("openai", "ollama", "vllm", "deepseek")
            else None
        )
        api_key = os.getenv("OPENAI_API_KEY") or config_api_key
        if provider in ("openai", "deepseek") and not api_key:
            raise ValueError(
                f"{provider} provider requires OPENAI_API_KEY to be set. "
                "For local models, use CLAUDE_API_PROVIDER=ollama or vllm."
            )
        config = APIClientConfig(
            provider=APIProvider.OPENAI,
            api_key=api_key or "dummy",
            base_url=base_url,
        )
    elif provider == "bedrock":
        config = APIClientConfig(
            provider=APIProvider.AWS_BEDROCK,
            aws_region=os.getenv("AWS_REGION") or app_config.aws_region or "us-east-1",
            aws_profile=os.getenv("AWS_PROFILE") or app_config.aws_profile,
        )
    elif provider == "vertex":
        config = APIClientConfig(
            provider=APIProvider.GOOGLE_VERTEX,
            vertex_project=os.getenv("VERTEX_PROJECT") or app_config.vertex_project,
            vertex_location=(
                os.getenv("VERTEX_LOCATION")
                or app_config.vertex_location
                or "us-central1"
            ),
        )
    elif provider == "azure":
        raise ValueError(
            "Azure provider is temporarily unavailable in this build. "
            "Use anthropic/bedrock/vertex provider until azure adapter is fully wired."
        )
    else:
        raise ValueError(f"Unknown provider: {provider}")
    
    # Validate API key
    if not config.api_key and config.provider == APIProvider.ANTHROPIC:
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable not set. "
            "Please set it with your API key."
        )
    
    return APIClient(config)


def build_system_prompt(working_dir: Optional[str] = None) -> str:
    """Build the system prompt.
    
    Args:
        working_dir: Optional working directory for context.
        
    Returns:
        System prompt string.
    """
    builder = ContextBuilder(working_dir)
    
    parts = [
        """You are Claude Code, an AI assistant that helps with software development tasks.

You have access to tools that let you read, write, and execute code. When working with files:
- Always prefer reading files over describing what they contain
- Use exact file paths and be precise with code changes
- When editing code, be careful about indentation and whitespace

When executing commands:
- Prefer safe, read-only operations when possible
- Ask for confirmation before destructive operations
- Provide clear feedback about what you're doing

Communication style:
- Be concise and practical
- Explain what you're doing, not just what you did
- When stuck, explain the issue and suggest alternatives""",
    ]

    runtime_scope = _resolve_memory_scope(os.getenv("CLAUDE_MEMORY_SCOPE"))
    memory = get_memory()
    memory_snapshot = memory.snapshot_scoped(
        runtime_scope,
        working_directory=working_dir or os.getcwd(),
        limit=12,
    )
    if memory_snapshot:
        snapshot_lines = [
            "Active memory snapshot:",
            f"- scope: {runtime_scope}",
        ]
        for key, value in memory_snapshot.items():
            snapshot_lines.append(f"- {key}: {value}")
        parts.append("\n".join(snapshot_lines))
    
    # Add context parts
    context_parts = builder.build_system_prompt_parts()
    parts.extend(context_parts)
    
    return "\n\n".join(parts)


def _create_application(app_config: Config) -> Application:
    """Create the canonical Application object for runtime ownership."""
    return Application(
        AppConfig(
            service_name="claude-code-python",
            version="1.0.0",
            log_level="DEBUG" if app_config.verbose else "INFO",
            enable_telemetry=app_config.enable_telemetry,
        )
    )


def _attach_runtime_services(
    engine: QueryEngine,
    *,
    session_manager: SessionManager,
    history_manager: HistoryManager,
    task_manager: TaskManager,
    hooks_manager: HooksManager,
    memory: SessionMemory,
    event_journal: EventJournal | SQLiteEventJournal,
) -> None:
    """Attach runtime services to QueryEngine for downstream command wiring."""
    engine.session_manager = session_manager  # type: ignore[attr-defined]
    engine.history_manager = history_manager  # type: ignore[attr-defined]
    engine.task_manager = task_manager  # type: ignore[attr-defined]
    engine.hooks_manager = hooks_manager  # type: ignore[attr-defined]
    engine.memory = memory  # type: ignore[attr-defined]
    engine.event_journal = event_journal  # type: ignore[attr-defined]


def create_runtime(
    model: Optional[str] = None,
    working_dir: Optional[str] = None,
) -> RuntimeContext:
    """Create full runtime context through a single bootstrap path."""
    resolved_working_dir = working_dir or os.getcwd()

    # Load app config once and propagate into runtime
    app_config = get_config()
    api_client = setup_api_client(app_config)

    # Get model from arg, config, then environment fallback
    if model is None:
        model = app_config.model or os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

    # Build query config with permission propagation
    query_config = QueryConfig(
        model=model,
        max_tokens=8192,
        system_prompt=build_system_prompt(resolved_working_dir),
        permission_mode=app_config.permission_mode.value if app_config.permission_mode else "default",
        always_allow=list(app_config.always_allow),
        always_deny=list(app_config.always_deny),
        working_directory=resolved_working_dir,
        memory_scope=_resolve_memory_scope(os.getenv("CLAUDE_MEMORY_SCOPE")),
    )

    tool_registry = create_default_registry()
    query_engine = QueryEngine(
        api_client=api_client,
        config=query_config,
        tool_registry=tool_registry,
    )

    runtime_state_db = Path(resolved_working_dir) / ".claude" / "runtime_state.db"
    session_store = SQLiteSessionStore(runtime_state_db)
    session_manager = SessionManager.from_store(session_store)
    current_session = session_manager.ensure_current_session()
    current_session.metadata.working_directory = resolved_working_dir
    current_session.metadata.model = model
    query_engine.config.session_id = current_session.id

    history_manager = HistoryManager(
        storage_path=Path(resolved_working_dir) / ".claude" / "history.json"
    )
    event_journal = SQLiteEventJournal(runtime_state_db)

    task_manager = create_task_manager_with_event_journal(
        TaskBackendConfig(
            working_directory=resolved_working_dir,
            queue_backend="memory",
            runtime_backend="sqlite",
        ),
        event_journal=event_journal,
    )
    hooks_manager = HooksManager(
        config_path=Path(resolved_working_dir) / ".claude" / "hooks.json"
    )
    memory = get_memory()

    _attach_runtime_services(
        query_engine,
        session_manager=session_manager,
        history_manager=history_manager,
        task_manager=task_manager,
        hooks_manager=hooks_manager,
        memory=memory,
        event_journal=event_journal,
    )

    return RuntimeContext(
        application=_create_application(app_config),
        app_config=app_config,
        api_client=api_client,
        tool_registry=tool_registry,
        query_engine=query_engine,
        session_manager=session_manager,
        history_manager=history_manager,
        task_manager=task_manager,
        hooks_manager=hooks_manager,
        memory=memory,
        event_journal=event_journal,
        working_directory=resolved_working_dir,
    )


def create_engine(
    model: Optional[str] = None,
    working_dir: Optional[str] = None,
) -> QueryEngine:
    """Create a query engine with default configuration.
    
    Args:
        model: Optional model override.
        working_dir: Optional working directory.
        
    Returns:
        Configured QueryEngine instance.
    """
    runtime = create_runtime(model=model, working_dir=working_dir)
    return runtime.query_engine


def _build_default_daemon_url(host: str, port: int) -> str:
    """Build daemon base URL from host/port."""
    return f"http://{host}:{port}"


def _resolve_daemon_client_mode(args: argparse.Namespace) -> DaemonClientMode:
    """Resolve daemon thin-client mode from CLI args and environment."""
    env_url = (os.getenv("CLAUDE_DAEMON_URL") or "").strip()
    cli_url = (args.daemon_url or "").strip()
    default_url = _build_default_daemon_url(args.daemon_host, args.daemon_port)
    base_url = cli_url or env_url or default_url
    enabled = bool(args.daemon_client or cli_url or env_url)
    return DaemonClientMode(
        enabled=enabled,
        base_url=base_url,
        timeout_seconds=float(args.daemon_timeout),
        required=bool(args.daemon_required),
    )


async def _query_via_daemon(
    query: str,
    *,
    base_url: str,
    timeout_seconds: float,
) -> str:
    """Execute a single query through daemon control-plane client."""
    from claude_code.server.control_plane import ControlPlaneClient

    client = ControlPlaneClient(base_url, timeout_seconds=timeout_seconds)
    response = await asyncio.to_thread(client.query, query)
    return str(response.get("output", ""))


async def run_pipe_mode_daemon(
    *,
    base_url: str,
    timeout_seconds: float,
) -> int:
    """Run pipe mode via daemon thin client."""
    user_input = sys.stdin.read()
    if not user_input.strip():
        return 0
    output = await _query_via_daemon(
        user_input,
        base_url=base_url,
        timeout_seconds=timeout_seconds,
    )
    if output:
        sys.stdout.write(output)
        sys.stdout.flush()
    return 0


async def run_single_query_daemon(
    query: str,
    *,
    base_url: str,
    timeout_seconds: float,
) -> int:
    """Run single query mode via daemon thin client."""
    output = await _query_via_daemon(
        query,
        base_url=base_url,
        timeout_seconds=timeout_seconds,
    )
    if output:
        print(output)
    return 0


async def run_repl(
    model: Optional[str] = None,
    verbose: bool = False,
    system: Optional[str] = None,
) -> None:
    """Run the interactive REPL.
    
    Args:
        model: Optional model override.
        verbose: Enable verbose output.
        system: Optional system prompt override.
    """
    engine = create_engine(model=model, working_dir=os.getcwd())
    
    # Add custom system prompt if provided
    if system:
        engine.config.system_prompt = system
    
    config = REPLConfig(
        verbose=verbose,
        stream_output=True,
        working_directory=os.getcwd(),
    )
    
    repl = REPL(engine, config)
    await repl.run()


async def run_pipe_mode(
    model: Optional[str] = None,
    verbose: bool = False,
) -> int:
    """Run in pipe mode (stdin to stdout).
    
    Args:
        model: Optional model override.
        verbose: Enable verbose output.
        
    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    engine = create_engine(model=model, working_dir=os.getcwd())
    pipe = PipeMode(engine)
    return await pipe.run()


async def run_single_query(
    query: str,
    model: Optional[str] = None,
    verbose: bool = False,
    system: Optional[str] = None,
) -> int:
    """Run a single query and print result to stdout."""
    engine = create_engine(model=model, working_dir=os.getcwd())
    if system:
        engine.config.system_prompt = system
    
    output_parts: list[str] = []
    try:
        async for event in engine.query(query):
            if isinstance(event, dict) and event.get("type") == "text":
                output_parts.append(str(event.get("content", "")))
            elif hasattr(event, "role") and getattr(event, "role", None) == "assistant":
                content = getattr(event, "content", "")
                if isinstance(content, str):
                    output_parts.append(content)
                elif isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            output_parts.append(str(block.get("text", "")))
        if output_parts:
            print("".join(output_parts))
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


async def run_doctor() -> None:
    """Run health check / diagnostics.
    
    Displays system status including:
    - Python version
    - API key configuration
    - Working directory
    - Git repository status
    - Model availability
    """
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    
    table = Table(title="Claude Code Health Check")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="dim")
    
    # Check Python version
    version = sys.version_info
    table.add_row("Python Version", "OK", f"{version.major}.{version.minor}.{version.micro}")

    interpreter_diag = _collect_interpreter_diagnostics()
    interpreter_status = "WARN" if interpreter_diag.has_windowsapps_stub_risk else "OK"
    table.add_row(
        "Interpreter",
        interpreter_status,
        " ; ".join(
            [
                f"sys.executable={interpreter_diag.executable} ({interpreter_diag.executable_source})",
                (
                    "python on PATH="
                    + (interpreter_diag.python_on_path or "N/A")
                    + f" ({interpreter_diag.python_on_path_source})"
                ),
            ]
        ),
    )
    if interpreter_diag.warning:
        table.add_row("Interpreter Risk", "WARN", interpreter_diag.warning)
    if sys.platform == "win32":
        table.add_row("Windows Launcher", "INFO", interpreter_diag.recommended_launcher)
    
    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        table.add_row("API Key", "OK", f"Set ({masked})")
    else:
        table.add_row("API Key", "MISSING", "Not set - set ANTHROPIC_API_KEY")
    
    # Check working directory
    cwd = os.getcwd()
    table.add_row("Working Directory", "OK", cwd)
    
    # Check git status
    git_info = ContextBuilder(cwd).get_system_context()
    if "gitStatus" in git_info:
        table.add_row("Git Repository", "OK", "Git repo detected")
    else:
        table.add_row("Git Repository", "N/A", "Not a git repository")
    
    # Check model availability
    try:
        runtime = create_runtime(working_dir=cwd)
        engine = runtime.query_engine
        table.add_row("API Connection", "OK", "Engine initialized")
    except Exception as e:
        table.add_row("API Connection", "ERROR", str(e))
    
    console.print(table)


def main() -> None:
    """Main entry point.
    
    Supports multiple modes:
    - Interactive REPL (default)
    - Pipe mode (-p flag)
    - Single query mode (positional args)
    - Doctor mode (--doctor flag)
    - Init mode (--init flag)
    """
    _configure_windows_console_encoding()
    
    parser = argparse.ArgumentParser(
        description="Claude Code Python - AI Programming Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--model", "-m",
        help="Model to use (default: from CLAUDE_MODEL env or claude-sonnet-4-20250514)",
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output",
    )
    
    parser.add_argument(
        "--system",
        help="System prompt to use",
    )
    
    parser.add_argument(
        "--pipe", "-p",
        action="store_true",
        help="Run in pipe mode (stdin to stdout)",
    )
    
    parser.add_argument(
        "--doctor",
        action="store_true",
        help="Run health check",
    )
    
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize project with CLAUDE.md",
    )
    
    parser.add_argument(
        "--mcp-serve",
        action="store_true",
        help="Run as MCP server (STDIO mode) for external MCP clients",
    )

    parser.add_argument(
        "--daemon-serve",
        action="store_true",
        help="Run as local daemon/API control plane server",
    )

    parser.add_argument(
        "--daemon-host",
        default="127.0.0.1",
        help="Daemon bind host (default: 127.0.0.1)",
    )

    parser.add_argument(
        "--daemon-port",
        type=int,
        default=8787,
        help="Daemon bind port (default: 8787)",
    )

    parser.add_argument(
        "--daemon-timeout",
        type=float,
        default=30.0,
        help="Daemon request timeout in seconds (default: 30.0)",
    )

    parser.add_argument(
        "--daemon-client",
        action="store_true",
        help="Use local daemon/API control plane as thin client for non-REPL query paths",
    )

    parser.add_argument(
        "--daemon-url",
        default=None,
        help=(
            "Daemon base URL for thin-client mode "
            "(default from CLAUDE_DAEMON_URL or --daemon-host/--daemon-port)"
        ),
    )

    parser.add_argument(
        "--daemon-required",
        action="store_true",
        help="Fail instead of falling back to local runtime when daemon thin-client call fails",
    )
    
    parser.add_argument(
        "--mcp-name",
        default="claude-code-python",
        help="Name of the MCP server (default: claude-code-python)",
    )
    
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version",
    )
    
    parser.add_argument(
        "args",
        nargs="*",
        help="Additional arguments (query in non-pipe mode)",
    )
    
    args = parser.parse_args()
    
    # Show version
    if args.version:
        print("Claude Code Python v1.0.0")
        print("AI Programming Assistant - Python implementation")
        return
    
    # Run init
    if args.init:
        from claude_code.commands.init import InitCommand
        from claude_code.commands.base import CommandContext
        from rich.console import Console
        
        console = Console()
        cmd = InitCommand()
        ctx = CommandContext(working_directory=os.getcwd(), console=console)
        result = asyncio.run(cmd.execute("", ctx))
        console.print(result.content)
        return
    
    # Run doctor
    if args.doctor:
        asyncio.run(run_doctor())
        return

    if args.daemon_serve:
        from claude_code.server.control_plane import run_control_plane_daemon

        runtime = create_runtime(model=args.model, working_dir=os.getcwd())
        run_control_plane_daemon(
            runtime,
            host=args.daemon_host,
            port=args.daemon_port,
            request_timeout_seconds=args.daemon_timeout,
        )
        return

    # Run MCP server
    if args.mcp_serve:
        from claude_code.mcp.server import run_mcp_server
        runtime = create_runtime(model=args.model, working_dir=os.getcwd())
        asyncio.run(run_mcp_server(
            working_directory=os.getcwd(),
            server_name=args.mcp_name,
            tool_registry=runtime.tool_registry,
        ))
        return
    
    # Initialize commands
    setup_default_commands()
    
    daemon_client_mode = _resolve_daemon_client_mode(args)

    # Pipe mode
    if args.pipe:
        if daemon_client_mode.enabled:
            try:
                exit_code = asyncio.run(
                    run_pipe_mode_daemon(
                        base_url=daemon_client_mode.base_url,
                        timeout_seconds=daemon_client_mode.timeout_seconds,
                    )
                )
                sys.exit(exit_code)
            except Exception as exc:
                if daemon_client_mode.required:
                    print(f"Error: daemon thin-client request failed: {exc}", file=sys.stderr)
                    sys.exit(1)
                if args.verbose:
                    print(
                        f"[daemon-fallback] thin-client request failed, fallback to local runtime: {exc}",
                        file=sys.stderr,
                    )

        exit_code = asyncio.run(run_pipe_mode(
            model=args.model,
            verbose=args.verbose,
        ))
        sys.exit(exit_code)
    
    # REPL mode
    query = " ".join(args.args) if args.args else None
    
    if query:
        # Single query mode
        if daemon_client_mode.enabled:
            try:
                exit_code = asyncio.run(
                    run_single_query_daemon(
                        query=query,
                        base_url=daemon_client_mode.base_url,
                        timeout_seconds=daemon_client_mode.timeout_seconds,
                    )
                )
                sys.exit(exit_code)
            except Exception as exc:
                if daemon_client_mode.required:
                    print(f"Error: daemon thin-client request failed: {exc}", file=sys.stderr)
                    sys.exit(1)
                if args.verbose:
                    print(
                        f"[daemon-fallback] thin-client request failed, fallback to local runtime: {exc}",
                        file=sys.stderr,
                    )

        exit_code = asyncio.run(run_single_query(
            query=query,
            model=args.model,
            verbose=args.verbose,
            system=args.system,
        ))
        sys.exit(exit_code)
    else:
        # Interactive REPL
        asyncio.run(run_repl(
            model=args.model,
            verbose=args.verbose,
            system=args.system,
        ))


if __name__ == "__main__":
    main()

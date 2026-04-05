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
from typing import Optional

# Fix Windows console encoding for Rich
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from claude_code.api.client import APIClient, APIClientConfig, APIProvider
from claude_code.engine.query import QueryEngine, QueryConfig
from claude_code.engine.context import ContextBuilder, PermissionMode, PermissionContext
from claude_code.repl import REPL, REPLConfig, PipeMode
from claude_code.tools.registry import create_default_registry
from claude_code.commands.registry import setup_default_commands
from claude_code.config import get_config, Config


def setup_api_client() -> APIClient:
    """Setup the API client based on environment.
    
    Reads from environment variables:
    - CLAUDE_API_PROVIDER: anthropic/bedrock/vertex/azure
    - ANTHROPIC_API_KEY: API key for Anthropic
    - AWS_REGION, AWS_PROFILE: For Bedrock
    - VERTEX_PROJECT, VERTEX_LOCATION: For Vertex
    - AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_API_KEY: For Azure
    
    Returns:
        Configured APIClient instance.
        
    Raises:
        ValueError: If required environment variables are missing.
    """
    # Check for API provider
    provider = os.getenv("CLAUDE_API_PROVIDER", "anthropic").lower()
    
    # Build config based on provider
    if provider == "anthropic":
        config = APIClientConfig(
            provider=APIProvider.ANTHROPIC,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        )
    elif provider == "bedrock":
        config = APIClientConfig(
            provider=APIProvider.AWS_BEDROCK,
            aws_region=os.getenv("AWS_REGION", "us-east-1"),
            aws_profile=os.getenv("AWS_PROFILE"),
        )
    elif provider == "vertex":
        config = APIClientConfig(
            provider=APIProvider.GOOGLE_VERTEX,
            vertex_project=os.getenv("VERTEX_PROJECT"),
            vertex_location=os.getenv("VERTEX_LOCATION", "us-central1"),
        )
    elif provider == "azure":
        config = APIClientConfig(
            provider=APIProvider.AZURE,
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-01-01"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
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
    
    # Add context parts
    context_parts = builder.build_system_prompt_parts()
    parts.extend(context_parts)
    
    return "\n\n".join(parts)


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
    api_client = setup_api_client()
    
    # Get model from arg or environment
    if model is None:
        model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
    
    # Build query config
    query_config = QueryConfig(
        model=model,
        max_tokens=8192,
        system_prompt=build_system_prompt(working_dir),
    )
    
    # Get tools from environment or use defaults
    tool_registry = create_default_registry()
    
    engine = QueryEngine(
        api_client=api_client,
        config=query_config,
        tool_registry=tool_registry,
    )
    
    return engine


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
    engine = create_engine(model=model)
    
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
    engine = create_engine(model=model)
    pipe = PipeMode(engine)
    return await pipe.run()


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
        engine = create_engine()
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
    
    # Initialize commands
    setup_default_commands()
    
    # Pipe mode
    if args.pipe:
        exit_code = asyncio.run(run_pipe_mode(
            model=args.model,
            verbose=args.verbose,
        ))
        sys.exit(exit_code)
    
    # REPL mode
    query = " ".join(args.args) if args.args else None
    
    if query:
        # Single query mode
        asyncio.run(run_repl(
            model=args.model,
            verbose=args.verbose,
            system=args.system,
        ))
    else:
        # Interactive REPL
        asyncio.run(run_repl(
            model=args.model,
            verbose=args.verbose,
            system=args.system,
        ))


if __name__ == "__main__":
    main()

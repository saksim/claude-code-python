"""
Claude Code Python - Init Command
Initialize a project with CLAUDE.md and other configurations.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- pathlib.Path for file operations
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from claude_code.commands.base import Command, CommandContext, CommandResult, CommandType
from claude_code.context.builder import ContextBuilder


class InitCommand(Command):
    """Initialize a project with CLAUDE.md configuration.
    
    Creates a CLAUDE.md file in the project directory with
    placeholder content for project-specific guidance.
    """
    
    def __init__(self) -> None:
        """Initialize the init command."""
        super().__init__(
            name="init",
            description="Initialize project with CLAUDE.md and configurations",
            command_type=CommandType.PROMPT,
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the init command.
        
        Args:
            args: Command arguments (unused for init).
            context: The command execution context.
            
        Returns:
            CommandResult with initialization status.
        """
        project_path = context.working_directory
        
        claude_md_path = Path(project_path) / "CLAUDE.md"
        local_md_path = Path(project_path) / "CLAUDE.local.md"
        
        if claude_md_path.exists() and local_md_path.exists():
            return CommandResult(
                content="""# Project Already Initialized

Found existing CLAUDE.md files:
- CLAUDE.md (project)
- CLAUDE.local.md (personal)

To modify, edit these files directly or use /memory command.""",
            )
        
        new_content = """# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Add a brief description of your project here.

## Commands

Add commonly used commands:
- Build: ...
- Test: ...
- Run: ...

## Architecture

Add high-level architecture notes.
"""
        
        if not claude_md_path.exists():
            with open(claude_md_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            return CommandResult(
                content=f"""# Project Initialized

Created CLAUDE.md at: {claude_md_path}

The file contains placeholder content. You can edit it to add:
- Project overview
- Build/test commands
- Architecture notes
- Any other guidance for Claude

To customize further, edit the file directly or run /init again.""",
            )
        
        return CommandResult(content="Project already has CLAUDE.md")


class DoctorCommand(Command):
    """Run health checks on the Claude Code setup.
    
    Checks API key configuration, config file presence,
    and MCP server setup.
    """
    
    def __init__(self) -> None:
        """Initialize the doctor command."""
        super().__init__(
            name="doctor",
            description="Run health checks",
            command_type=CommandType.LOCAL,
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the doctor command.
        
        Args:
            args: Command arguments (unused for doctor).
            context: The command execution context.
            
        Returns:
            CommandResult with health check results.
        """
        lines: list[str] = ["# Health Check\n"]
        
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            lines.append("✓ API Key: Configured")
        else:
            lines.append("✗ API Key: Not configured")
        
        config_path = Path.home() / ".claude-code-python" / "config.json"
        if config_path.exists():
            lines.append("✓ Config: Found")
        else:
            lines.append("○ Config: Not found (will use defaults)")
        
        mcp_path = Path(context.working_directory) / ".mcp.json"
        if mcp_path.exists():
            lines.append("✓ MCP: Config file found")
        else:
            lines.append("○ MCP: No servers configured")
        
        return CommandResult(content="\n".join(lines))


class VersionCommand(Command):
    """Show Claude Code Python version information.
    
    Aliases: --version, -v
    """
    
    def __init__(self) -> None:
        """Initialize the version command."""
        super().__init__(
            name="version",
            description="Show version information",
            command_type=CommandType.LOCAL,
            aliases=["--version", "-v"],
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the version command.
        
        Args:
            args: Command arguments (unused for version).
            context: The command execution context.
            
        Returns:
            CommandResult with version information.
        """
        return CommandResult(content="""Claude Code Python
Version: 0.1.0 (pre-alpha)

This is a Python implementation of Claude Code CLI.
Based on reverse-engineered TypeScript source.""")


def create_init_command() -> InitCommand:
    """Create the init command.
    
    Returns:
        A new InitCommand instance.
    """
    return InitCommand()


def create_doctor_command() -> DoctorCommand:
    """Create the doctor command.
    
    Returns:
        A new DoctorCommand instance.
    """
    return DoctorCommand()


def create_version_command() -> VersionCommand:
    """Create the version command.
    
    Returns:
        A new VersionCommand instance.
    """
    return VersionCommand()

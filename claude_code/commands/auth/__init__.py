"""
Claude Code Python - Auth Commands
Login and logout functionality.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
"""

from __future__ import annotations

import os
from typing import Any

from claude_code.commands.base import Command, CommandContext, CommandResult, CommandType


class LoginCommand(Command):
    """Login to Claude Code using API key.
    
    Guides the user through the login process with Anthropic API key.
    Aliases: signin
    """
    
    def __init__(self) -> None:
        """Initialize the login command."""
        super().__init__(
            name="login",
            description="Login to Claude Code using OAuth",
            command_type=CommandType.LOCAL,
            aliases=["signin"],
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the login command.
        
        Args:
            args: Command arguments (unused for login).
            context: The command execution context.
            
        Returns:
            CommandResult with login instructions.
        """
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        api_url = os.environ.get("ANTHROPIC_API_URL")
        
        if api_key:
            return CommandResult(
                content="You are already logged in. Use /logout to sign out first.",
            )
        
        return CommandResult(content="""# Login to Claude Code

To login, you need an Anthropic API key:

1. Visit https://console.anthropic.com/settings/keys
2. Create a new API key
3. Set it as an environment variable:

   export ANTHROPIC_API_KEY="sk-ant-api03-..."

Or add it to your config:

   claude config set api_key "sk-ant-api03-..."

For more login options, visit the documentation.""")
    
    def _check_existing_login(self) -> str | None:
        """Check if user is already logged in.
        
        Returns:
            Masked API key if logged in, None otherwise.
        """
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        
        if api_key:
            if api_key.startswith("sk-ant-"):
                return f"sk-ant-{'*' * 20}{api_key[-4:]}"
        
        return None


class LogoutCommand(Command):
    """Logout from Claude Code.
    
    Removes stored API key and clears environment variables.
    Aliases: signout
    """
    
    def __init__(self) -> None:
        """Initialize the logout command."""
        super().__init__(
            name="logout",
            description="Logout from Claude Code",
            command_type=CommandType.LOCAL,
            aliases=["signout"],
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the logout command.
        
        Args:
            args: Command arguments (unused for logout).
            context: The command execution context.
            
        Returns:
            CommandResult indicating logout success.
        """
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        
        if not api_key:
            return CommandResult(content="You are not logged in.")
        
        config = ConfigManager()
        saved_key = config.get("api_key")
        
        if saved_key:
            config.set("api_key", None)
        
        os.environ.pop("ANTHROPIC_API_KEY", None)
        
        return CommandResult(content="Logged out successfully.")


class AuthStatusCommand(Command):
    """Check current authentication status.
    
    Shows whether user is logged in and provides masked
    API key information.
    """
    
    def __init__(self) -> None:
        """Initialize the auth status command."""
        super().__init__(
            name="auth",
            description="Check authentication status",
            command_type=CommandType.LOCAL,
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the auth status command.
        
        Args:
            args: Command arguments (unused for auth status).
            context: The command execution context.
            
        Returns:
            CommandResult with authentication status.
        """
        from claude_code.api.client import APIClient, APIClientConfig
        
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        
        config = ConfigManager()
        saved_key = config.get("api_key")
        
        has_key = bool(api_key or saved_key)
        
        if has_key:
            masked = "sk-ant-***" if (api_key or saved_key) else None
            return CommandResult(content=f"""# Authentication Status

Status: Logged in
API Key: {masked}

To logout: claude logout
""")
        else:
            return CommandResult(content="""# Authentication Status

Status: Not logged in

To login, visit: https://console.anthropic.com/settings/keys
""")


def create_auth_commands() -> dict[str, Command]:
    """Create authentication-related commands.
    
    Returns:
        Dictionary of auth command instances.
    """
    return {
        "login": LoginCommand(),
        "logout": LogoutCommand(),
        "auth": AuthStatusCommand(),
    }

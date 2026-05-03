"""
Claude Code Python - Auth Commands
Login and logout functionality.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
"""

from __future__ import annotations

import os

from claude_code.commands.base import Command, CommandContext, CommandResult, CommandType
from claude_code.config import get_config, save_config


_OPENAI_FAMILY_PROVIDERS: set[str] = {"openai", "ollama", "vllm", "deepseek"}
_KEYLESS_PROVIDERS: set[str] = {"bedrock", "vertex"}
_ALL_KEY_ENV_VARS: tuple[str, ...] = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "AZURE_OPENAI_API_KEY")


def _resolve_provider() -> str:
    """Resolve active provider using runtime precedence."""
    config = get_config()
    provider = os.getenv("CLAUDE_API_PROVIDER", getattr(config, "api_provider", "anthropic"))
    return str(provider).lower()


def _provider_env_key(provider: str) -> str | None:
    """Return provider-specific API key environment variable name."""
    if provider == "anthropic":
        return "ANTHROPIC_API_KEY"
    if provider in _OPENAI_FAMILY_PROVIDERS:
        return "OPENAI_API_KEY"
    if provider == "azure":
        return "AZURE_OPENAI_API_KEY"
    return None


def _is_config_key_usable(provider: str, config_provider: str) -> bool:
    """Check whether persisted config.api_key is applicable for active provider."""
    if provider == "anthropic":
        return config_provider == "anthropic"
    if provider in _OPENAI_FAMILY_PROVIDERS:
        return config_provider in _OPENAI_FAMILY_PROVIDERS
    if provider == "azure":
        return config_provider == "azure"
    return False


def _resolve_auth_key() -> tuple[str, str | None, str | None]:
    """Resolve runtime authentication key and its source.

    Returns:
        Tuple of (provider, key, source) where source is "env", "config", or None.
    """
    config = get_config()
    provider = _resolve_provider()
    env_key_name = _provider_env_key(provider)
    env_key_value = os.getenv(env_key_name) if env_key_name else None

    config_provider = str(getattr(config, "api_provider", "anthropic")).lower()
    config_api_key = getattr(config, "api_key", None)
    config_key_value = config_api_key if _is_config_key_usable(provider, config_provider) else None

    if env_key_value:
        return provider, env_key_value, "env"
    if config_key_value:
        return provider, str(config_key_value), "config"
    return provider, None, None


def _mask_key(key: str) -> str:
    """Mask API key for display."""
    if len(key) <= 8:
        return "*" * len(key)
    suffix = key[-4:] if len(key) > 12 else key[-2:]
    return f"{key[:8]}...{suffix}"


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
        provider, api_key, source = _resolve_auth_key()

        if provider in _KEYLESS_PROVIDERS:
            return CommandResult(
                content=(
                    "# Login to Claude Code\n\n"
                    f"Provider `{provider}` uses cloud credentials and does not require an API key.\n"
                    "No /login action is required."
                ),
            )

        if api_key:
            source_label = "environment variable" if source == "env" else "config file"
            return CommandResult(
                content=(
                    "You are already logged in.\n\n"
                    f"Provider: {provider}\n"
                    f"Source: {source_label}\n"
                    f"Key: {_mask_key(api_key)}\n\n"
                    "Use /logout to sign out first."
                ),
            )

        env_key_name = _provider_env_key(provider) or "ANTHROPIC_API_KEY"
        if provider == "anthropic":
            login_help = (
                "1. Visit https://console.anthropic.com/settings/keys\n"
                "2. Create a new API key\n"
                "3. Set environment variable:\n\n"
                f'   export {env_key_name}="sk-ant-api03-..."\n'
            )
        else:
            login_help = (
                "Set your API key as environment variable:\n\n"
                f'   export {env_key_name}="<your-api-key>"\n'
            )

        return CommandResult(
            content=(
                "# Login to Claude Code\n\n"
                f"Active provider: {provider}\n\n"
                f"{login_help}\n"
                "Or persist in config:\n\n"
                '   claude config set api_key "<your-api-key>"\n'
            ),
        )


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
        cleared_sources: list[str] = []

        for env_key in _ALL_KEY_ENV_VARS:
            if os.environ.pop(env_key, None) is not None:
                cleared_sources.append(f"env:{env_key}")

        config = get_config()
        if getattr(config, "api_key", None):
            config.api_key = None
            save_config()
            cleared_sources.append("config:api_key")

        if not cleared_sources:
            return CommandResult(content="You are not logged in.")

        return CommandResult(
            content=(
                "Logged out successfully.\n\n"
                "Cleared sources:\n"
                + "\n".join(f"- {source}" for source in cleared_sources)
            ),
        )


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
        provider, api_key, source = _resolve_auth_key()
        env_key_name = _provider_env_key(provider)

        if provider in _KEYLESS_PROVIDERS:
            return CommandResult(
                content=(
                    "# Authentication Status\n\n"
                    "Status: Credential-based\n"
                    f"Provider: {provider}\n"
                    "API Key: not required\n\n"
                    "This provider uses cloud credentials instead of API keys."
                ),
            )

        if api_key:
            source_label = "environment variable" if source == "env" else "config file"
            return CommandResult(
                content=(
                    "# Authentication Status\n\n"
                    "Status: Logged in\n"
                    f"Provider: {provider}\n"
                    f"Source: {source_label}\n"
                    f"API Key: {_mask_key(api_key)}\n\n"
                    "To logout: claude logout"
                ),
            )

        return CommandResult(
            content=(
                "# Authentication Status\n\n"
                "Status: Not logged in\n"
                f"Provider: {provider}\n"
                f"Expected Key: {env_key_name or 'N/A'}\n\n"
                f"To login, set {env_key_name or 'an appropriate key env var'} "
                "or run: claude config set api_key \"<your-api-key>\""
            ),
        )


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

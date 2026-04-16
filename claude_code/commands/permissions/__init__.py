"""
Claude Code Python - Permissions Command

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
"""

from __future__ import annotations

from typing import Any

from claude_code.commands.base import Command, CommandContext, CommandResult, CommandType
from claude_code.permissions import PermissionMode
from claude_code.config import get_config, LocalSettings


class PermissionsCommand(Command):
    """Manage tool permissions.
    
    Provides subcommands to view and modify permission settings,
    including permission mode and tool-specific rules.
    Aliases: perms
    """
    
    def __init__(self) -> None:
        """Initialize the permissions command."""
        super().__init__(
            name="permissions",
            description="Manage tool permissions",
            command_type=CommandType.LOCAL,
            aliases=["perms"],
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the permissions command.
        
        Args:
            args: Command arguments (subcommand and its args).
            context: The command execution context.
            
        Returns:
            CommandResult with subcommand output.
        """
        args = args.strip()
        
        if not args:
            return await self._show_status(context)
        
        parts = args.split()
        subcmd = parts[0]
        
        if subcmd == "set":
            if len(parts) < 2:
                return CommandResult(success=False, error="Usage: /permissions set <mode>")
            return await self._set_mode(parts[1], context)
        
        if subcmd == "allow":
            if len(parts) < 2:
                return CommandResult(success=False, error="Usage: /permissions allow <tool>")
            return await self._allow_tool(" ".join(parts[1:]), context)
        
        if subcmd == "deny":
            if len(parts) < 2:
                return CommandResult(success=False, error="Usage: /permissions deny <tool>")
            return await self._deny_tool(" ".join(parts[1:]), context)
        
        if subcmd == "list":
            return await self._list_rules(context)
        
        return CommandResult(success=False, error=f"Unknown: {subcmd}")
    
    async def _show_status(self, context: CommandContext) -> CommandResult:
        """Show current permission status.
        
        Args:
            context: The command execution context.
            
        Returns:
            CommandResult with permission status.
        """
        settings = LocalSettings(context.working_directory)
        mode = settings.permission_mode
        
        modes: dict[str, str] = {
            "default": "Ask for permission before each tool",
            "auto": "Auto-approve safe operations",
            "plan": "Ask for permission for everything",
            "bypass": "No permission checks",
            "yolo": "No restrictions at all",
        }
        
        lines: list[str] = ["# Permissions\n", f"Mode: {mode}\n", f"Description: {modes.get(mode, 'Unknown')}\n"]
        
        always_allow = settings.always_allow
        if always_allow:
            lines.append(f"\nAlways Allow: {', '.join(always_allow)}")
        
        always_deny = settings.always_deny
        if always_deny:
            lines.append(f"\nAlways Deny: {', '.join(always_deny)}")
        
        return CommandResult(content="\n".join(lines))
    
    async def _set_mode(self, mode: str, context: CommandContext) -> CommandResult:
        """Set the permission mode.
        
        Args:
            mode: Permission mode to set.
            context: The command execution context.
            
        Returns:
            CommandResult indicating success.
        """
        valid: list[str] = ["default", "auto", "plan", "bypass", "yolo"]
        if mode not in valid:
            return CommandResult(success=False, error=f"Invalid mode: {mode}")
        
        settings = LocalSettings(context.working_directory)
        settings.permission_mode = mode
        settings.save()
        
        return CommandResult(content=f"Permission mode set to: {mode}")
    
    async def _allow_tool(self, tool: str, context: CommandContext) -> CommandResult:
        """Add a tool to the always-allow list.
        
        Args:
            tool: Name of the tool to allow.
            context: The command execution context.
            
        Returns:
            CommandResult indicating success.
        """
        settings = LocalSettings(context.working_directory)
        allow = settings.always_allow
        
        if tool not in allow:
            allow.append(tool)
            settings.always_allow = allow
            settings.save()
        
        return CommandResult(content=f"Added {tool} to always allow list")
    
    async def _deny_tool(self, tool: str, context: CommandContext) -> CommandResult:
        """Add a tool to the always-deny list.
        
        Args:
            tool: Name of the tool to deny.
            context: The command execution context.
            
        Returns:
            CommandResult indicating success.
        """
        settings = LocalSettings(context.working_directory)
        deny = settings.always_deny
        
        if tool not in deny:
            deny.append(tool)
            settings.always_deny = deny
            settings.save()
        
        return CommandResult(content=f"Added {tool} to always deny list")
    
    async def _list_rules(self, context: CommandContext) -> CommandResult:
        """List all permission rules.
        
        Args:
            context: The command execution context.
            
        Returns:
            CommandResult with permission rules.
        """
        return await self._show_status(context)


def create_permissions_command() -> PermissionsCommand:
    """Create the permissions command.
    
    Returns:
        A new PermissionsCommand instance.
    """
    return PermissionsCommand()


__all__ = ["PermissionsCommand", "create_permissions_command"]

"""
Claude Code Python - Hooks Command
"""

from __future__ import annotations

from pathlib import Path

from claude_code.commands.base import Command, CommandContext, CommandResult, CommandType
from claude_code.services.hooks_manager import HookEvent, HooksManager


class HooksCommand(Command):
    """Manage hooks."""
    
    def __init__(self):
        super().__init__(
            name="hooks",
            description="Manage hooks",
            command_type=CommandType.LOCAL,
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        args = args.strip()
        
        if not args:
            return await self._list_hooks(context)
        
        parts = args.split()
        subcmd = parts[0]
        
        if subcmd == "list":
            return await self._list_hooks(context)
        
        if subcmd == "add":
            if len(parts) < 3:
                return CommandResult(success=False, error="Usage: /hooks add <event> <command>")
            return await self._add_hook(parts[1], " ".join(parts[2:]), context)
        
        if subcmd == "remove":
            if len(parts) < 2:
                return CommandResult(success=False, error="Usage: /hooks remove <name>")
            return await self._remove_hook(parts[1], context)
        
        return CommandResult(success=False, error=f"Unknown: {subcmd}")
    
    def _resolve_manager(self, context: CommandContext) -> HooksManager:
        engine = getattr(context, "engine", None)
        manager = getattr(engine, "hooks_manager", None)
        if (
            manager is not None
            and hasattr(manager, "list_hooks")
            and hasattr(manager, "add_hook")
            and hasattr(manager, "remove_hook")
        ):
            return manager

        hooks_file = Path(context.working_directory) / ".claude" / "hooks.json"
        return HooksManager(config_path=hooks_file)

    def _parse_event(self, raw_event: str) -> HookEvent | None:
        normalized = raw_event.strip().lower().replace("-", "_")
        for event in HookEvent:
            if normalized == event.value:
                return event
        return None

    def _next_hook_name(self, manager: HooksManager) -> str:
        existing = {hook.name for hook in manager.list_hooks(include_disabled=True)}
        candidate = 1
        while True:
            name = f"hook-{candidate}"
            if name not in existing:
                return name
            candidate += 1

    async def _list_hooks(self, context: CommandContext) -> CommandResult:
        manager = self._resolve_manager(context)
        hooks = manager.list_hooks(include_disabled=True)
        if not hooks:
            return CommandResult(content="No hooks configured")

        lines = ["# Hooks\n"]
        for hook in hooks:
            lines.append(f"\n## {hook.name}")
            lines.append(f"Event: {hook.event.value}")
            lines.append(f"Command: {hook.command}")
            lines.append(f"Enabled: {hook.enabled}")
            lines.append(f"Timeout: {hook.timeout_seconds}s")
        
        return CommandResult(content="\n".join(lines))
    
    async def _add_hook(self, event: str, command: str, context: CommandContext) -> CommandResult:
        parsed_event = self._parse_event(event)
        if parsed_event is None:
            allowed_events = ", ".join(h.value for h in HookEvent)
            return CommandResult(
                success=False,
                error=f"Invalid event '{event}'. Allowed events: {allowed_events}",
            )

        manager = self._resolve_manager(context)
        name = self._next_hook_name(manager)
        manager.add_hook(
            name=name,
            event=parsed_event,
            command=command,
        )
        return CommandResult(content=f"Added hook: {name}")
    
    async def _remove_hook(self, name: str, context: CommandContext) -> CommandResult:
        manager = self._resolve_manager(context)
        removed = manager.remove_hook(name)
        if not removed:
            return CommandResult(success=False, error=f"Hook not found: {name}")

        return CommandResult(content=f"Removed hook: {name}")


def create_hooks_command() -> HooksCommand:
    return HooksCommand()


__all__ = ["HooksCommand", "create_hooks_command"]

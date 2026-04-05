"""
Claude Code Python - Hooks Command
"""

from __future__ import annotations

import json
from pathlib import Path

from claude_code.commands.base import Command, CommandContext, CommandResult, CommandType


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
    
    async def _list_hooks(self, context: CommandContext) -> CommandResult:
        hooks_file = Path(context.working_directory) / ".claude" / "hooks.json"
        
        if not hooks_file.exists():
            return CommandResult(content="No hooks configured")
        
        with open(hooks_file) as f:
            hooks = json.load(f)
        
        if not hooks:
            return CommandResult(content="No hooks configured")
        
        lines = ["# Hooks\n"]
        for name, config in hooks.items():
            lines.append(f"\n## {name}")
            lines.append(f"Event: {config.get('event', 'N/A')}")
            lines.append(f"Command: {config.get('command', 'N/A')}")
        
        return CommandResult(content="\n".join(lines))
    
    async def _add_hook(self, event: str, command: str, context: CommandContext) -> CommandResult:
        hooks_dir = Path(context.working_directory) / ".claude"
        hooks_dir.mkdir(exist_ok=True)
        hooks_file = hooks_dir / "hooks.json"
        
        hooks = {}
        if hooks_file.exists():
            with open(hooks_file) as f:
                hooks = json.load(f)
        
        name = f"hook-{len(hooks) + 1}"
        hooks[name] = {"event": event, "command": command}
        
        with open(hooks_file, "w") as f:
            json.dump(hooks, f, indent=2)
        
        return CommandResult(content=f"Added hook: {name}")
    
    async def _remove_hook(self, name: str, context: CommandContext) -> CommandResult:
        hooks_file = Path(context.working_directory) / ".claude" / "hooks.json"
        
        if not hooks_file.exists():
            return CommandResult(success=False, error="No hooks configured")
        
        with open(hooks_file) as f:
            hooks = json.load(f)
        
        if name not in hooks:
            return CommandResult(success=False, error=f"Hook not found: {name}")
        
        del hooks[name]
        
        with open(hooks_file, "w") as f:
            json.dump(hooks, f, indent=2)
        
        return CommandResult(content=f"Removed hook: {name}")


def create_hooks_command() -> HooksCommand:
    return HooksCommand()


__all__ = ["HooksCommand", "create_hooks_command"]

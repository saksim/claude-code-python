"""
Claude Code Python - Model and Theme Commands
"""

from __future__ import annotations

import os
from typing import Optional

from claude_code.commands.base import Command, CommandContext, CommandResult, CommandType
from claude_code.config import get_config, save_config


MODELS = {
    "haiku": "claude-haiku-20240307",
    "sonnet": "claude-sonnet-4-20250514",
    "opus": "claude-opus-4-20250514",
    "sonnet-4": "claude-sonnet-4-20250514",
    "opus-4": "claude-opus-4-20250514",
}


class ModelCommand(Command):
    """Model selection."""
    
    def __init__(self):
        super().__init__(
            name="model",
            description="Select model",
            command_type=CommandType.LOCAL,
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        args = args.strip()
        
        if not args:
            config = get_config()
            current = config.model
            for name, full in MODELS.items():
                if full == current:
                    current = name
                    break
            lines = ["# Current Model\n", f"{current}\n", "\n# Available Models\n"]
            for name in MODELS:
                lines.append(f"- {name}")
            return CommandResult(content="\n".join(lines))
        
        if args not in MODELS:
            return CommandResult(success=False, error=f"Unknown model: {args}")
        
        config = get_config()
        config.model = MODELS[args]
        save_config()
        
        return CommandResult(content=f"Model set to {args}")


class ThemeCommand(Command):
    """Theme management."""
    
    def __init__(self):
        super().__init__(
            name="theme",
            description="Manage terminal theme",
            command_type=CommandType.LOCAL,
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        args = args.strip()
        
        themes = {
            "default": {"fg": "white", "bg": "black"},
            "dark": {"fg": "bright_white", "bg": "black"},
            "light": {"fg": "black", "bg": "white"},
            "monochrome": {"fg": "white", "bg": "black"},
        }
        
        if not args:
            lines = ["# Available Themes\n"]
            for name, colors in themes.items():
                lines.append(f"- {name}: {colors}")
            return CommandResult(content="\n".join(lines))
        
        if args not in themes:
            return CommandResult(success=False, error=f"Unknown theme: {args}")
        
        from claude_code.config import LocalSettings
        settings = LocalSettings(context.working_directory)
        settings.set("theme", args)
        settings.save()
        
        return CommandResult(content=f"Theme set to {args}")


class ModelsCommand(Command):
    """List available models (alias)."""
    
    def __init__(self):
        super().__init__(
            name="models",
            description="List available models",
            command_type=CommandType.LOCAL,
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        lines = ["# Available Models\n"]
        for name, full in MODELS.items():
            lines.append(f"- {name}: {full}")
        return CommandResult(content="\n".join(lines))


def create_model_command() -> ModelCommand:
    return ModelCommand()

def create_theme_command() -> ThemeCommand:
    return ThemeCommand()


__all__ = ["ModelCommand", "ThemeCommand", "create_model_command", "create_theme_command"]

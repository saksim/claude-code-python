"""
Claude Code Python - Skills Command
"""

from __future__ import annotations

import json
from pathlib import Path

from claude_code.commands.base import Command, CommandContext, CommandResult, CommandType


class SkillsCommand(Command):
    """Manage skills."""
    
    def __init__(self):
        super().__init__(
            name="skills",
            description="Manage skills",
            command_type=CommandType.LOCAL,
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        args = args.strip()
        
        if not args:
            return await self._list_skills(context)
        
        parts = args.split()
        subcmd = parts[0]
        
        if subcmd == "list":
            return await self._list_skills(context)
        
        if subcmd == "add":
            if len(parts) < 2:
                return CommandResult(success=False, error="Usage: /skills add <name>")
            return await self._add_skill(" ".join(parts[1:]), context)
        
        if subcmd == "remove":
            if len(parts) < 2:
                return CommandResult(success=False, error="Usage: /skills remove <name>")
            return await self._remove_skill(" ".join(parts[1:]), context)
        
        return CommandResult(success=False, error=f"Unknown: {subcmd}")
    
    async def _list_skills(self, context: CommandContext) -> CommandResult:
        skills_dir = Path(context.working_directory) / ".claude" / "skills"
        
        if not skills_dir.exists():
            return CommandResult(content="No skills directory found")
        
        skills = list(skills_dir.glob("*.md"))
        
        if not skills:
            return CommandResult(content="No skills found")
        
        lines = ["# Skills\n"]
        for s in skills:
            lines.append(f"- {s.stem}")
        
        return CommandResult(content="\n".join(lines))
    
    async def _add_skill(self, name: str, context: CommandContext) -> CommandResult:
        skills_dir = Path(context.working_directory) / ".claude" / "skills"
        skills_dir.mkdir(exist_ok=True)
        
        skill_file = skills_dir / f"{name}.md"
        
        if skill_file.exists():
            return CommandResult(success=False, error=f"Skill already exists: {name}")
        
        skill_file.write_text(f"""# Skill: {name}

Describe what this skill does...

## Usage

/how-use-this-skill

## Examples

Example 1: ...
""")
        
        return CommandResult(content=f"Created skill: {name}")
    
    async def _remove_skill(self, name: str, context: CommandContext) -> CommandResult:
        skills_dir = Path(context.working_directory) / ".claude" / "skills"
        skill_file = skills_dir / f"{name}.md"
        
        if not skill_file.exists():
            return CommandResult(success=False, error=f"Skill not found: {name}")
        
        skill_file.unlink()
        
        return CommandResult(content=f"Removed skill: {name}")


def create_skills_command() -> SkillsCommand:
    return SkillsCommand()


__all__ = ["SkillsCommand", "create_skills_command"]

"""
Claude Code Python - Skill Tool
Invoke and manage skills.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- pathlib.Path for file operations
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from claude_code.tools.base import Tool, ToolContext, ToolResult, ToolCallback
from claude_code.skills.registry import SkillRegistry


class SkillTool(Tool):
    """Tool to invoke and manage skills.
    
    This tool allows users to invoke reusable prompt templates (skills)
    during a conversation. Skills can accept arguments that are
    substituted into the prompt template.
    
    Attributes:
        name: skill
        description: Invoke a skill by name. Skills are reusable prompt templates.
    """
    
    def __init__(self, registry: Optional[SkillRegistry] = None) -> None:
        """Initialize the skill tool.
        
        Args:
            registry: Optional skill registry to use.
        """
        super().__init__()
        self._registry = registry
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "skill"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "Invoke a skill by name. Skills are reusable prompt templates."
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input.
        
        Returns:
            JSON schema defining the input parameters.
        """
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the skill to invoke"
                },
                "arguments": {
                    "type": "object",
                    "description": "Key-value arguments to substitute in the skill prompt"
                }
            },
            "required": ["name"]
        }
    
    def is_read_only(self) -> bool:
        """Tool reads skills but doesn't modify system state.
        
        Returns:
            True since invoking skills is a read operation.
        """
        return True
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the skill invocation.
        
        Args:
            input_data: Dictionary with 'name' and optional 'arguments'.
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with the skill prompt content.
        """
        skill_name = input_data.get("name", "")
        arguments = input_data.get("arguments", {})
        
        if not skill_name:
            return ToolResult(
                content="Error: skill name is required",
                is_error=True
            )
        
        from claude_code.skills.registry import get_skill_registry
        registry = self._registry or get_skill_registry()
        
        skill = registry.get(skill_name)
        
        if skill is None:
            available = [s.name for s in registry.list_all()]
            avail_text = ", ".join(available) if available else "none"
            return ToolResult(
                content=f"Skill '{skill_name}' not found.\n\nAvailable skills: {avail_text}",
                is_error=True
            )
        
        content = skill.prompt
        
        if arguments:
            for key, value in arguments.items():
                content = content.replace(f"{{{key}}}", str(value))
                content = content.replace(f"${{{key}}}", str(value))
        
        return ToolResult(
            content=f"# Skill: {skill_name}\n\n{content}"
        )


class ListSkillsTool(Tool):
    """Tool to list available skills.
    
    This tool displays all available skills in the registry,
    with optional filtering by category or search term.
    
    Attributes:
        name: list_skills
        description: List all available skills
    """
    
    def __init__(self, registry: Optional[SkillRegistry] = None) -> None:
        """Initialize the list skills tool.
        
        Args:
            registry: Optional skill registry to use.
        """
        super().__init__()
        self._registry = registry
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "list_skills"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "List all available skills"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input.
        
        Returns:
            JSON schema defining the input parameters.
        """
        return {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Filter skills by category"
                },
                "search": {
                    "type": "string",
                    "description": "Search skills by name or description"
                }
            },
            "required": []
        }
    
    def is_read_only(self) -> bool:
        """Tool only reads skill information.
        
        Returns:
            True since listing is a read operation.
        """
        return True
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the skills listing.
        
        Args:
            input_data: Dictionary with optional 'category' and 'search'.
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with list of available skills.
        """
        category = input_data.get("category")
        search = input_data.get("search")
        
        from claude_code.skills.registry import get_skill_registry
        registry = self._registry or get_skill_registry()
        
        skills = registry.list_all()
        
        if category:
            skills = [s for s in skills if s.category == category]
        
        if search:
            skills = registry.search(search)
        
        if not skills:
            return ToolResult(content="No skills found")
        
        lines = ["# Available Skills\n"]
        for skill in skills:
            lines.append(f"\n## {skill.name}")
            lines.append(f"Description: {skill.description}")
            if skill.category:
                lines.append(f"Category: {skill.category}")
            if skill.tags:
                lines.append(f"Tags: {', '.join(skill.tags)}")
        
        return ToolResult(content="\n".join(lines))


class DiscoverSkillsTool(Tool):
    """Tool to discover skills from the filesystem.
    
    This tool scans the filesystem for skill definitions and
    registers them with the skill registry.
    
    Attributes:
        name: discover_skills
        description: Discover and load skills from the filesystem
    """
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "discover_skills"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "Discover and load skills from the filesystem"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input.
        
        Returns:
            JSON schema defining the input parameters.
        """
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path to scan for skills"
                }
            },
            "required": []
        }
    
    def is_read_only(self) -> bool:
        """Tool modifies system state by discovering skills.
        
        Returns:
            False since this tool registers skills in the registry.
        """
        return False
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the skills discovery.
        
        Args:
            input_data: Dictionary with optional 'path'.
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with discovery results.
        """
        path = input_data.get("path", context.working_directory)
        
        skills_dir = Path(path) / ".claude" / "skills"
        
        if not skills_dir.exists():
            return ToolResult(content="No .claude/skills directory found")
        
        from claude_code.skills.registry import get_skill_registry
        from claude_code.skills.models import create_skill_from_markdown
        
        registry = get_skill_registry()
        
        discovered = 0
        for md_file in skills_dir.glob("*.md"):
            try:
                skill = create_skill_from_markdown(md_file.read_text(), str(md_file))
                registry.register(skill)
                discovered += 1
            except Exception:
                pass
        
        return ToolResult(content=f"Discovered {discovered} skills from {skills_dir}")


def get_default_skills_tools() -> list[Tool]:
    """Get default skills tools."""
    return [
        SkillTool(),
        ListSkillsTool(),
        DiscoverSkillsTool(),
    ]


__all__ = [
    "SkillTool",
    "ListSkillsTool",
    "DiscoverSkillsTool",
    "get_default_skills_tools",
]

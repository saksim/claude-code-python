"""
Skill definitions for Claude Code Python.

Skills are reusable workflows that can be invoked by the user.
Following TOP Python Dev standards:
- Dataclass patterns (frozen/slots where appropriate)
- Comprehensive type hints
- Detailed docstrings
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from pathlib import Path


class SkillSource(Enum):
    """Source of a skill.
    
    Attributes:
        BUNDLED: Skills bundled with Claude Code
        USER: User-defined skills
        PROJECT: Project-specific skills
        PLUGIN: Skills from plugins
        MCP: Skills from MCP servers
    """
    BUNDLED = "bundled"
    USER = "user"
    PROJECT = "project"
    PLUGIN = "plugin"
    MCP = "mcp"


@dataclass(frozen=True)
class Skill:
    """
    A skill definition.
    
    Skills are reusable workflows that can be invoked by the user.
    They contain a prompt that guides the AI in performing specific tasks.
    
    Attributes:
        name: Unique identifier for the skill
        description: Human-readable description of what the skill does
        source: Origin of the skill (bundled, user, project, etc.)
        content: The prompt/content of the skill
        files: List of file paths related to the skill
        user_invocable: Whether users can invoke this skill directly
        enabled: Whether the skill is active
        category: Category for organizing skills
        tags: List of tags for filtering/searching
        prompt: Alias for content (for bundled skills)
        examples: Example invocations
        required_tools: Tools needed to execute this skill
        compatibility: Compatibility information
    """
    name: str
    description: str
    source: SkillSource = SkillSource.USER
    content: str = ""
    files: list[str] = field(default_factory=list)
    user_invocable: bool = True
    enabled: bool = True
    category: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    prompt: str = ""
    examples: list[str] = field(default_factory=list)
    required_tools: list[str] = field(default_factory=list)
    compatibility: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert skill to dictionary representation.
        
        Returns:
            Dictionary with skill properties suitable for serialization.
        """
        return {
            "name": self.name,
            "description": self.description,
            "source": self.source.value,
            "files": self.files,
            "userInvocable": self.user_invocable,
            "enabled": self.enabled,
            "category": self.category,
            "tags": self.tags,
            "prompt": self.prompt,
            "examples": self.examples,
            "required_tools": self.required_tools,
            "compatibility": self.compatibility,
        }


@dataclass
class SkillInvocation:
    """An invocation of a skill.
    
    Represents a single execution of a skill with its parameters
    and execution context.
    
    Attributes:
        skill_name: Name of the skill being invoked
        args: Arguments passed to the skill
        context: Execution context information
        invocation_id: Unique identifier for this invocation
    """
    skill_name: str
    args: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    invocation_id: str = ""


@dataclass(frozen=True)
class BundledSkillSpec:
    """Specification for a bundled skill.
    
    Immutable specification for skills that are bundled with Claude Code.
    These skills provide specialized capabilities for specific domains.
    
    Attributes:
        name: Unique identifier for the bundled skill
        description: Human-readable description
        prompt: The skill prompt content
        category: Category for organization
        tags: List of tags for filtering
        required_tools: Tools needed to execute this skill
        examples: Example invocations
    """
    name: str
    description: str
    prompt: str
    category: str
    tags: list[str] = field(default_factory=list)
    required_tools: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    
    def to_skill(self) -> Skill:
        """Convert this spec to a Skill instance.
        
        Returns:
            Skill object with properties from this specification.
        """
        return Skill(
            name=self.name,
            description=self.description,
            source=SkillSource.BUNDLED,
            content=self.prompt,
            category=self.category,
            tags=self.tags,
            prompt=self.prompt,
            required_tools=self.required_tools,
            examples=self.examples,
        )


def parse_skill_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from skill content.
    
    Extracts metadata from markdown files that use YAML frontmatter
    for defining skill properties.
    
    Args:
        content: Raw markdown content with optional frontmatter.
        
    Returns:
        Tuple of (frontmatter dict, body content after frontmatter).
        Returns ({}, content) if no valid frontmatter found.
    """
    lines = content.split('\n')
    
    if not lines or lines[0].strip() != '---':
        return {}, content
    
    end_idx: int | None = None
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == '---':
            end_idx = i
            break
    
    if end_idx is None:
        return {}, content
    
    try:
        import yaml
        frontmatter = yaml.safe_load('\n'.join(lines[1:end_idx]))
        body = '\n'.join(lines[end_idx + 1:])
        return (frontmatter or {}), body
    except ImportError:
        return {}, content
    except yaml.YAMLError:
        return {}, content


def create_skill_from_markdown(
    name: str,
    content: str,
    source: SkillSource = SkillSource.USER,
) -> Skill:
    """Create a skill from markdown content.
    
    Parses markdown content with YAML frontmatter to create a Skill.
    The frontmatter should contain: description, category, tags, etc.
    
    Args:
        name: Name for the skill
        content: Raw markdown content with frontmatter
        source: Source of the skill (default: user-defined)
        
    Returns:
        Skill instance populated from frontmatter and content.
    """
    frontmatter, body = parse_skill_frontmatter(content)
    
    return Skill(
        name=name,
        description=frontmatter.get('description', ''),
        content=body.strip(),
        source=source,
        category=frontmatter.get('category'),
        tags=frontmatter.get('tags', []),
        user_invocable=frontmatter.get('userInvocable', True),
        enabled=frontmatter.get('enabled', True),
    )

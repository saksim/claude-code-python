"""
Skill registry for Claude Code Python.

Manages registration and loading of skills.
"""

import os
import glob
import importlib.util
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass, field

from claude_code.skills.models import Skill, SkillSource, create_skill_from_markdown
from claude_code.skills.builtin import get_all_builtin_skills, get_top_skills


class SkillRegistry:
    """
    Registry for managing skills.
    
    Handles skill registration, discovery, and loading.
    """
    
    def __init__(self):
        self._skills: dict[str, Skill] = {}
        self._skill_loaders: list[Callable[[], list[Skill]]] = []
    
    def register(self, skill: Skill) -> None:
        """Register a skill."""
        self._skills[skill.name] = skill
    
    def unregister(self, name: str) -> bool:
        """Unregister a skill."""
        if name in self._skills:
            del self._skills[name]
            return True
        return False
    
    def get(self, name: str) -> Optional[Skill]:
        """Get a skill by name."""
        return self._skills.get(name)
    
    def list_all(self) -> list[Skill]:
        """List all registered skills."""
        return list(self._skills.values())
    
    def list_by_source(self, source: SkillSource) -> list[Skill]:
        """List skills by source."""
        return [s for s in self._skills.values() if s.source == source]
    
    def list_by_category(self, category: str) -> list[Skill]:
        """List skills by category."""
        return [s for s in self._skills.values() if s.category == category]
    
    def search(self, query: str) -> list[Skill]:
        """Search skills by name or description."""
        query_lower = query.lower()
        results = []
        
        for skill in self._skills.values():
            if query_lower in skill.name.lower():
                results.append(skill)
            elif query_lower in skill.description.lower():
                results.append(skill)
            elif any(query_lower in tag.lower() for tag in skill.tags):
                results.append(skill)
        
        return results
    
    def add_loader(self, loader: Callable[[], list[Skill]]) -> None:
        """Add a skill loader function."""
        self._skill_loaders.append(loader)
    
    def load_all(self) -> int:
        """Load all skills using registered loaders."""
        total = 0
        for loader in self._skill_loaders:
            skills = loader()
            for skill in skills:
                self.register(skill)
                total += 1
        return total
    
    def clear(self) -> None:
        """Clear all skills."""
        self._skills.clear()


class SkillLoader:
    """
    Loads skills from various sources.
    
    Supports loading skills from:
    - Directory of .md files
    - Bundled skill modules
    - MCP servers
    """
    
    def __init__(self, registry: Optional[SkillRegistry] = None):
        self.registry = registry or get_skill_registry()
    
    def load_from_directory(
        self,
        directory: str,
        source: SkillSource = SkillSource.USER,
    ) -> list[Skill]:
        """Load skills from a directory of .md files."""
        skills = []
        
        if not os.path.isdir(directory):
            return skills
        
        # Find SKILL.md files
        for skill_dir in glob.glob(os.path.join(directory, "*", "SKILL.md")):
            skill_path = Path(skill_dir)
            skill_name = skill_path.parent.name
            
            try:
                with open(skill_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                skill = create_skill_from_markdown(skill_name, content, source)
                
                # Load associated files
                skill_dir_path = skill_path.parent
                for md_file in skill_dir_path.glob("*.md"):
                    if md_file.name != "SKILL.md":
                        skill.files.append(str(md_file))
                
                # Look for examples directory
                examples_dir = skill_dir_path / "examples"
                if examples_dir.is_dir():
                    for example_file in examples_dir.glob("*.md"):
                        skill.files.append(str(example_file))
                
                skills.append(skill)
                self.registry.register(skill)
                
            except Exception:
                continue
        
        # Also check for single .md files (legacy format)
        for md_file in glob.glob(os.path.join(directory, "*.md")):
            if os.path.basename(md_file) == "SKILL.md":
                continue
            
            skill_name = Path(md_file).stem
            
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                skill = create_skill_from_markdown(skill_name, content, source)
                skills.append(skill)
                self.registry.register(skill)
                
            except Exception:
                continue
        
        return skills
    
    def load_bundled_skills(self) -> list[Skill]:
        """Load bundled skills including TOP-level skills."""
        # Use the comprehensive builtin skills
        skills = get_all_builtin_skills()
        
        # Register all skills
        for skill in skills:
            self.registry.register(skill)
        
        return skills
    
    def load_from_project(self, project_dir: str) -> list[Skill]:
        """Load skills from project's .claude/skills directory."""
        skills_dir = os.path.join(project_dir, ".claude", "skills")
        return self.load_from_directory(skills_dir, SkillSource.PROJECT)
    
    def load_from_user(self) -> list[Skill]:
        """Load skills from user's config directory."""
        config_dir = os.path.expanduser("~/.claude/skills")
        return self.load_from_directory(config_dir, SkillSource.USER)


# Global registry
_registry: Optional[SkillRegistry] = None


def get_skill_registry() -> SkillRegistry:
    """Get the global skill registry."""
    global _registry
    if _registry is None:
        _registry = SkillRegistry()
    return _registry


def set_skill_registry(registry: SkillRegistry) -> None:
    """Set the global skill registry."""
    global _registry
    _registry = registry


def load_all_skills(
    project_dir: Optional[str] = None,
    include_bundled: bool = True,
) -> SkillRegistry:
    """
    Load all skills from all sources.
    
    Args:
        project_dir: Project directory to load project skills from
        include_bundled: Whether to include bundled skills
        
    Returns:
        The skill registry with all loaded skills
    """
    registry = get_skill_registry()
    loader = SkillLoader(registry)
    
    if include_bundled:
        loader.load_bundled_skills()
    
    loader.load_from_user()
    
    if project_dir:
        loader.load_from_project(project_dir)
    
    return registry

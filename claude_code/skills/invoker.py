"""
Skill invoker for Claude Code Python.

Handles the execution of skills.
"""

import os
from typing import Optional, Any, Callable
from dataclasses import dataclass, field

from claude_code.skills.models import Skill, SkillInvocation
from claude_code.skills.registry import get_skill_registry, SkillRegistry


@dataclass
class SkillResult:
    """Result from skill execution."""
    success: bool
    skill_name: str
    output: str = ""
    error: Optional[str] = None
    duration_ms: float = 0


class SkillInvoker:
    """
    Invokes skills and manages skill execution.
    
    Handles loading skill content and preparing prompts.
    """
    
    def __init__(self, registry: Optional[SkillRegistry] = None):
        self.registry = registry or get_skill_registry()
        self._pre_invoke_hooks: list[Callable[[str, str], None]] = []
        self._post_invoke_hooks: list[Callable[[str, SkillResult], None]] = []
    
    def add_pre_invoke_hook(self, hook: Callable[[str, str], None]) -> None:
        """Add a hook to run before skill invocation."""
        self._pre_invoke_hooks.append(hook)
    
    def add_post_invoke_hook(self, hook: Callable[[str, SkillResult], None]) -> None:
        """Add a hook to run after skill invocation."""
        self._post_invoke_hooks.append(hook)
    
    async def invoke(
        self,
        skill_name: str,
        args: str = "",
        context: Optional[dict] = None,
    ) -> SkillResult:
        """
        Invoke a skill by name.
        
        Args:
            skill_name: Name of the skill to invoke
            args: Arguments to pass to the skill
            context: Additional context for the skill
            
        Returns:
            SkillResult with the skill output
        """
        import time
        start = time.time()
        
        # Get the skill
        skill = self.registry.get(skill_name)
        if not skill:
            return SkillResult(
                success=False,
                skill_name=skill_name,
                error=f"Skill not found: {skill_name}",
                duration_ms=0,
            )
        
        if not skill.enabled:
            return SkillResult(
                success=False,
                skill_name=skill_name,
                error=f"Skill is disabled: {skill_name}",
                duration_ms=0,
            )
        
        # Run pre-invoke hooks
        for hook in self._pre_invoke_hooks:
            try:
                hook(skill_name, args)
            except Exception:
                pass
        
        # Load skill content if not already loaded
        if not skill.content and skill.files:
            skill = self._load_skill_content(skill)
        
        # Generate the prompt
        prompt = self._generate_prompt(skill, args, context or {})
        
        duration_ms = (time.time() - start) * 1000
        
        result = SkillResult(
            success=True,
            skill_name=skill_name,
            output=prompt,
            duration_ms=duration_ms,
        )
        
        # Run post-invoke hooks
        for hook in self._post_invoke_hooks:
            try:
                hook(skill_name, result)
            except Exception:
                pass
        
        return result
    
    def _load_skill_content(self, skill: Skill) -> Skill:
        """Load skill content from files."""
        if not skill.files:
            return skill
        
        # Load the main SKILL.md file
        for file_path in skill.files:
            if file_path.endswith("SKILL.md"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        from claude_code.skills.models import parse_skill_frontmatter, create_skill_from_markdown
                        content = f.read()
                        
                        updated = create_skill_from_markdown(
                            skill.name,
                            content,
                            skill.source,
                        )
                        skill.description = updated.description
                        skill.content = updated.content
                        skill.tags = updated.tags
                        skill.category = updated.category
                except Exception:
                    pass
                break
        
        return skill
    
    def _generate_prompt(
        self,
        skill: Skill,
        args: str,
        context: dict,
    ) -> str:
        """Generate the prompt for a skill."""
        parts = []
        
        # Add skill content
        if skill.content:
            parts.append(skill.content)
        
        # Add user arguments
        if args:
            parts.append(f"## User Request\n\n{args}")
        
        # Add context if available
        if context:
            context_parts = []
            for key, value in context.items():
                context_parts.append(f"- {key}: {value}")
            
            if context_parts:
                parts.append(f"## Context\n\n" + "\n".join(context_parts))
        
        return "\n\n".join(parts)
    
    def get_skill_prompt(
        self,
        skill_name: str,
        args: str = "",
    ) -> Optional[str]:
        """
        Get the prompt for a skill without invoking it.
        
        Returns None if skill not found.
        """
        skill = self.registry.get(skill_name)
        if not skill:
            return None
        
        if not skill.content and skill.files:
            skill = self._load_skill_content(skill)
        
        return self._generate_prompt(skill, args, {})


def invoke_skill(
    skill_name: str,
    args: str = "",
    context: Optional[dict] = None,
) -> SkillResult:
    """Synchronous wrapper for invoking a skill."""
    import asyncio
    
    invoker = SkillInvoker()
    return asyncio.get_event_loop().run_until_complete(
        invoker.invoke(skill_name, args, context)
    )

"""
Claude Code Python - Skills System

Skills are reusable workflows that can be invoked by the user.

Skills can be:
- Bundled with Claude Code
- User-defined in ~/.claude/skills/
- Project-specific in .claude/skills/
- Provided by MCP servers

Example skill structure:
    skills/
    └── my-skill/
        ├── SKILL.md          # Main skill file
        └── examples/
            └── example.md     # Example usage

SKILL.md format:
    ---
    description: What this skill does
    category: testing
    tags: [testing, verification]
    userInvocable: true
    ---
    
    # Skill Content
    
    Describe what this skill does...
    
    ## When to Use
    
    When you need to...
"""

from claude_code.skills.models import (
    Skill,
    SkillSource,
    SkillInvocation,
    parse_skill_frontmatter,
    create_skill_from_markdown,
)

from claude_code.skills.registry import (
    SkillRegistry,
    SkillLoader,
    get_skill_registry,
    set_skill_registry,
    load_all_skills,
)

from claude_code.skills.invoker import (
    SkillInvoker,
    SkillResult,
    invoke_skill,
)

__all__ = [
    # Models
    "Skill",
    "SkillSource",
    "SkillInvocation",
    "parse_skill_frontmatter",
    "create_skill_from_markdown",
    
    # Registry
    "SkillRegistry",
    "SkillLoader",
    "get_skill_registry",
    "set_skill_registry",
    "load_all_skills",
    
    # Invoker
    "SkillInvoker",
    "SkillResult",
    "invoke_skill",
]


# Example bundled skills:
# 
# verify  - Run tests to verify code changes
# debug   - Debug an issue
# deploy  - Deploy the application
# review  - Review code changes
# refactor - Refactor code
# document - Generate documentation

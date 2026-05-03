"""Custom agent loader for .claude/agents markdown definitions."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml

from claude_code.agents.builtin import AgentDefinition


def _normalize_string_list(value: Any, *, default: list[str]) -> list[str]:
    """Normalize string list values from frontmatter."""
    if value is None:
        return list(default)
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else list(default)
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            if isinstance(item, str):
                text = item.strip()
                if text:
                    result.append(text)
        return result if result else list(default)
    return list(default)


def _parse_agent_markdown(filepath: Path) -> Optional[AgentDefinition]:
    """Parse a single agent markdown file with YAML frontmatter."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        return None

    if not content.startswith("---"):
        return None

    parts = content.split("---", 2)
    if len(parts) < 3:
        return None

    try:
        frontmatter = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None

    if not isinstance(frontmatter, dict):
        return None

    name = frontmatter.get("name")
    description = frontmatter.get("description")
    prompt = parts[2].strip()

    if not isinstance(name, str) or not name.strip():
        return None
    if not isinstance(description, str) or not description.strip():
        return None
    if not prompt:
        return None

    model = frontmatter.get("model", "sonnet")
    if not isinstance(model, str) or not model.strip():
        model = "sonnet"

    tools = _normalize_string_list(frontmatter.get("tools"), default=["*"])
    disallowed_tools = _normalize_string_list(
        frontmatter.get("disallowedTools", frontmatter.get("disallowed_tools")),
        default=[],
    )

    background_raw = frontmatter.get("background", False)
    background = bool(background_raw) if isinstance(background_raw, (bool, int)) else False

    permission_mode = frontmatter.get("permissionMode", frontmatter.get("permission_mode", "acceptEdits"))
    if not isinstance(permission_mode, str) or not permission_mode.strip():
        permission_mode = "acceptEdits"

    max_turns_raw = frontmatter.get("maxTurns", frontmatter.get("max_turns"))
    max_turns: int | None = None
    if isinstance(max_turns_raw, int) and max_turns_raw > 0:
        max_turns = max_turns_raw

    color = frontmatter.get("color")
    if not isinstance(color, str) or not color.strip():
        color = None

    isolation = frontmatter.get("isolation")
    if not isinstance(isolation, str) or isolation.strip() != "worktree":
        isolation = None
    else:
        isolation = "worktree"

    memory = frontmatter.get("memory")
    if not isinstance(memory, str):
        memory = None
    else:
        memory = memory.strip().lower()
        if memory not in {"user", "project", "local"}:
            memory = None

    omit_claude_md_raw = frontmatter.get(
        "omitClaudeMd",
        frontmatter.get("omit_claude_md", False),
    )
    omit_claude_md = bool(omit_claude_md_raw) if isinstance(omit_claude_md_raw, (bool, int)) else False

    return AgentDefinition(
        agent_type=name.strip(),
        description=description.strip(),
        prompt=prompt,
        model=model.strip(),
        background=background,
        isolation=isolation,
        permission_mode=permission_mode.strip(),
        color=color,
        tools=tools,
        disallowed_tools=disallowed_tools,
        max_turns=max_turns,
        memory=memory,
        omit_claude_md=omit_claude_md,
    )


def _discover_agent_directories(cwd: str | Path) -> list[Path]:
    """Discover .claude/agents directories from cwd up to git root."""
    resolved = Path(cwd).resolve()
    parent_chain = [resolved, *resolved.parents]
    found: list[Path] = []

    for current in parent_chain:
        agent_dir = current / ".claude" / "agents"
        if agent_dir.is_dir():
            found.append(agent_dir)
        if (current / ".git").exists():
            break

    # Load outermost first so deeper paths override duplicate agent names.
    return list(reversed(found))


def load_agents_from_directory(cwd: str | Path) -> dict[str, AgentDefinition]:
    """Load custom agents from .claude/agents directories."""
    agents: dict[str, AgentDefinition] = {}
    for agent_dir in _discover_agent_directories(cwd):
        for md_file in sorted(agent_dir.glob("*.md")):
            parsed = _parse_agent_markdown(md_file)
            if parsed is None:
                continue
            agents[parsed.agent_type] = parsed
    return agents


__all__ = ["load_agents_from_directory"]


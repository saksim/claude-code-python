import warnings
warnings.warn(f"{__name__} is deprecated and will be removed in a future version.", DeprecationWarning, stacklevel=2)
"""
Claude Code Python - Diagnostic Snapshots
Tool and command snapshots for diagnostics and parity tracking.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Dataclass patterns (frozen/slots)
- pathlib.Path for file operations
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass


# Module-level constants
SNAPSHOT_DIR: Path = Path(__file__).parent / "reference_data"
DEFAULT_SNAPSHOT_LIMIT: int = 20
DEFAULT_STATUS: str = "mirrored"
IMPLEMENTED_STATUS: str = "implemented"


@dataclass(frozen=True, slots=True)
class ToolSnapshot:
    """Tool snapshot entry.
    
    Using frozen=True, slots=True for immutability.
    
    Attributes:
        name: Tool name
        source_hint: Source of the tool (e.g., "claude_code_python")
        responsibility: Description of what the tool does
        status: Current status ("mirrored", "implemented", etc.)
    """
    name: str
    source_hint: str
    responsibility: str
    status: str = DEFAULT_STATUS


@dataclass(frozen=True, slots=True)
class CommandSnapshot:
    """Command snapshot entry.
    
    Using frozen=True, slots=True for immutability.
    
    Attributes:
        name: Command name
        source_hint: Source of the command
        command_type: Type of command (PROMPT, LOCAL, etc.)
        description: Command description
        status: Current status ("mirrored", "implemented", etc.)
    """
    name: str
    source_hint: str
    command_type: str
    description: str
    status: str = DEFAULT_STATUS


def load_tools_snapshot() -> list[dict[str, Any]]:
    """Load tools snapshot from reference data.
    
    Returns:
        List of tool snapshot dictionaries
    """
    snapshot_file = SNAPSHOT_DIR / "tools_snapshot.json"
    if snapshot_file.exists():
        return json.loads(snapshot_file.read_text(encoding="utf-8"))
    return []


def load_commands_snapshot() -> list[dict[str, Any]]:
    """Load commands snapshot from reference data.
    
    Returns:
        List of command snapshot dictionaries
    """
    snapshot_file = SNAPSHOT_DIR / "commands_snapshot.json"
    if snapshot_file.exists():
        return json.loads(snapshot_file.read_text(encoding="utf-8"))
    return []


def save_tools_snapshot(tools: list[dict[str, Any]]) -> None:
    """Save tools snapshot to reference data.
    
    Args:
        tools: List of tool snapshot dictionaries
    """
    snapshot_file = SNAPSHOT_DIR / "tools_snapshot.json"
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    with open(snapshot_file, "w", encoding="utf-8") as f:
        json.dump(tools, f, indent=2)


def save_commands_snapshot(commands: list[dict[str, Any]]) -> None:
    """Save commands snapshot to reference data.
    
    Args:
        commands: List of command snapshot dictionaries
    """
    snapshot_file = SNAPSHOT_DIR / "commands_snapshot.json"
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    with open(snapshot_file, "w", encoding="utf-8") as f:
        json.dump(commands, f, indent=2)


def generate_tools_snapshot() -> list[dict[str, Any]]:
    """Generate tools snapshot from current implementation.
    
    Returns:
        List of tool snapshots with current implementation status
    """
    from claude_code.tools import create_default_registry
    
    registry = create_default_registry()
    tools = registry.list_all()
    
    snapshot: list[dict[str, Any]] = []
    for tool in tools:
        snapshot.append({
            "name": tool.name,
            "source_hint": "claude_code_python",
            "responsibility": tool.description,
            "status": IMPLEMENTED_STATUS,
        })
    
    return snapshot


def generate_commands_snapshot() -> list[dict[str, Any]]:
    """Generate commands snapshot from current implementation.
    
    Returns:
        List of command snapshots with current implementation status
    """
    from claude_code.commands.registry import get_all_commands
    
    commands = get_all_commands()
    
    snapshot: list[dict[str, Any]] = []
    for name, cmd in commands.items():
        cmd_type = getattr(cmd, "command_type", None)
        type_value = cmd_type.value if hasattr(cmd_type, "value") else "prompt"
        snapshot.append({
            "name": cmd.name,
            "source_hint": "claude_code_python",
            "command_type": type_value,
            "description": cmd.description,
            "status": IMPLEMENTED_STATUS,
        })
    
    return snapshot


def render_tool_index(query: Optional[str] = None, limit: int = DEFAULT_SNAPSHOT_LIMIT) -> str:
    """Render tool index for display.
    
    Args:
        query: Optional search query
        limit: Maximum number of tools to display
        
    Returns:
        Formatted tool index string
    """
    tools = load_tools_snapshot()
    
    if query:
        query_lower = query.lower()
        tools = [t for t in tools if query_lower in t["name"].lower() or query_lower in t.get("responsibility", "").lower()]
    
    tools = tools[:limit]
    
    lines = [f"# Tool Index (Total: {len(load_tools_snapshot())})"]
    
    if query:
        lines.append(f"\nFiltered by: {query}")
    
    lines.append("")
    
    for tool in tools:
        status_icon = "✓" if tool.get("status") == IMPLEMENTED_STATUS else "○"
        lines.append(f"- [{status_icon}] {tool['name']}")
        lines.append(f"  Responsibility: {tool.get('responsibility', 'N/A')}")
        lines.append(f"  Source: {tool.get('source_hint', 'N/A')}")
        lines.append("")
    
    return "\n".join(lines)


def render_command_index(query: Optional[str] = None, limit: int = DEFAULT_SNAPSHOT_LIMIT) -> str:
    """Render command index for display.
    
    Args:
        query: Optional search query
        limit: Maximum number of commands to display
        
    Returns:
        Formatted command index string
    """
    commands = load_commands_snapshot()
    
    if query:
        query_lower = query.lower()
        commands = [c for c in commands if query_lower in c["name"].lower() or query_lower in c.get("description", "").lower()]
    
    commands = commands[:limit]
    
    lines = [f"# Command Index (Total: {len(load_commands_snapshot())})"]
    
    if query:
        lines.append(f"\nFiltered by: {query}")
    
    lines.append("")
    
    for cmd in commands:
        status_icon = "✓" if cmd.get("status") == IMPLEMENTED_STATUS else "○"
        lines.append(f"- [{status_icon}] /{cmd['name']}")
        lines.append(f"  Type: {cmd.get('command_type', 'N/A')}")
        lines.append(f"  Description: {cmd.get('description', 'N/A')}")
        lines.append("")
    
    return "\n".join(lines)


def compare_with_snapshot() -> dict[str, dict[str, int]]:
    """Compare current implementation with snapshots.
    
    Returns:
        Dictionary with tool and command comparison results
    """
    current_tools = generate_tools_snapshot()
    snapshot_tools = load_tools_snapshot()
    
    current_commands = generate_commands_snapshot()
    snapshot_commands = load_commands_snapshot()
    
    tool_names = {t["name"] for t in current_tools}
    snapshot_tool_names = {t["name"] for t in snapshot_tools}
    
    command_names = {c["name"] for c in current_commands}
    snapshot_command_names = {c["name"] for c in snapshot_commands}
    
    return {
        "tools": {
            "implemented": len(tool_names & snapshot_tool_names),
            "missing": len(snapshot_tool_names - tool_names),
            "extra": len(tool_names - snapshot_tool_names),
        },
        "commands": {
            "implemented": len(command_names & snapshot_command_names),
            "missing": len(snapshot_command_names - command_names),
            "extra": len(command_names - snapshot_command_names),
        },
    }


__all__ = [
    "ToolSnapshot",
    "CommandSnapshot",
    "load_tools_snapshot",
    "load_commands_snapshot",
    "save_tools_snapshot",
    "save_commands_snapshot",
    "generate_tools_snapshot",
    "generate_commands_snapshot",
    "render_tool_index",
    "render_command_index",
    "compare_with_snapshot",
]

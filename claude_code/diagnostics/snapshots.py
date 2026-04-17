"""Claude Code Python - Diagnostic Snapshots."""

from __future__ import annotations

import json
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

warnings.warn(
    f"{__name__} is deprecated and will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)


SNAPSHOT_DIR: Path = Path(__file__).parent / "reference_data"
DEFAULT_SNAPSHOT_LIMIT: int = 20
DEFAULT_STATUS: str = "mirrored"
IMPLEMENTED_STATUS: str = "implemented"


@dataclass(frozen=True, slots=True)
class ToolSnapshot:
    name: str
    source_hint: str
    responsibility: str
    status: str = DEFAULT_STATUS


@dataclass(frozen=True, slots=True)
class CommandSnapshot:
    name: str
    source_hint: str
    command_type: str
    description: str
    status: str = DEFAULT_STATUS


def _read_snapshot(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _write_snapshot(path: Path, payload: list[dict[str, Any]]) -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_tools_snapshot() -> list[dict[str, Any]]:
    return _read_snapshot(SNAPSHOT_DIR / "tools_snapshot.json")


def load_commands_snapshot() -> list[dict[str, Any]]:
    return _read_snapshot(SNAPSHOT_DIR / "commands_snapshot.json")


def save_tools_snapshot(tools: list[dict[str, Any]]) -> None:
    _write_snapshot(SNAPSHOT_DIR / "tools_snapshot.json", tools)


def save_commands_snapshot(commands: list[dict[str, Any]]) -> None:
    _write_snapshot(SNAPSHOT_DIR / "commands_snapshot.json", commands)


def generate_tools_snapshot() -> list[dict[str, Any]]:
    from claude_code.tools import create_default_registry

    registry = create_default_registry()
    tools = registry.list_all()
    return [
        {
            "name": tool.name,
            "source_hint": "claude_code_python",
            "responsibility": tool.description,
            "status": IMPLEMENTED_STATUS,
        }
        for tool in tools
    ]


def generate_commands_snapshot() -> list[dict[str, Any]]:
    from claude_code.commands.registry import get_all_commands

    commands = get_all_commands()
    snapshot: list[dict[str, Any]] = []
    for _, cmd in commands.items():
        cmd_type = getattr(cmd, "command_type", None)
        type_value = cmd_type.value if hasattr(cmd_type, "value") else "prompt"
        snapshot.append(
            {
                "name": cmd.name,
                "source_hint": "claude_code_python",
                "command_type": type_value,
                "description": cmd.description,
                "status": IMPLEMENTED_STATUS,
            }
        )
    return snapshot


def render_tool_index(query: Optional[str] = None, limit: int = DEFAULT_SNAPSHOT_LIMIT) -> str:
    tools = load_tools_snapshot()
    if query:
        q = query.lower()
        tools = [
            t
            for t in tools
            if q in t["name"].lower() or q in t.get("responsibility", "").lower()
        ]

    lines = [f"# Tool Index (Total: {len(load_tools_snapshot())})", ""]
    if query:
        lines.append(f"Filtered by: {query}")
        lines.append("")

    for tool in tools[:limit]:
        status = "[OK]" if tool.get("status") == IMPLEMENTED_STATUS else "[ ]"
        lines.append(f"- {status} {tool['name']}")
        lines.append(f"  Responsibility: {tool.get('responsibility', 'N/A')}")
        lines.append(f"  Source: {tool.get('source_hint', 'N/A')}")
        lines.append("")

    return "\n".join(lines)


def render_command_index(query: Optional[str] = None, limit: int = DEFAULT_SNAPSHOT_LIMIT) -> str:
    commands = load_commands_snapshot()
    if query:
        q = query.lower()
        commands = [
            c
            for c in commands
            if q in c["name"].lower() or q in c.get("description", "").lower()
        ]

    lines = [f"# Command Index (Total: {len(load_commands_snapshot())})", ""]
    if query:
        lines.append(f"Filtered by: {query}")
        lines.append("")

    for cmd in commands[:limit]:
        status = "[OK]" if cmd.get("status") == IMPLEMENTED_STATUS else "[ ]"
        lines.append(f"- {status} /{cmd['name']}")
        lines.append(f"  Type: {cmd.get('command_type', 'N/A')}")
        lines.append(f"  Description: {cmd.get('description', 'N/A')}")
        lines.append("")

    return "\n".join(lines)


def compare_with_snapshot() -> dict[str, dict[str, int]]:
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

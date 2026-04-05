"""
Claude Code Python - Porting Snapshots

Imports tool and command metadata from the parity workspace.
This provides a comprehensive reference for all available features.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Optional

# Path to parity snapshots - navigate up from claude_code/porting to parent dirs
_PARITY_ROOT = Path(__file__).resolve().parent.parent.parent.parent / "claw-code-parity"
SNAPSHOT_TOOLS_PATH = _PARITY_ROOT / "src" / "reference_data" / "tools_snapshot.json"
SNAPSHOT_COMMANDS_PATH = _PARITY_ROOT / "src" / "reference_data" / "commands_snapshot.json"


@dataclass(frozen=True, slots=True)
class PortingModule:
    """A module from the porting workspace.
    
    Attributes:
        name: Module name
        responsibility: Description of what the module does
        source_hint: Original TypeScript source path
        status: Porting status (planned, mirrored, completed)
    """
    name: str
    responsibility: str
    source_hint: str
    status: str = "planned"


@dataclass
class PortingBacklog:
    """A backlog of modules to be ported.
    
    Attributes:
        title: Backlog title
        modules: List of porting modules
    """
    title: str
    modules: list[PortingModule] = field(default_factory=list)

    def summary_lines(self) -> list[str]:
        """Get summary lines for the backlog."""
        return [
            f'- {module.name} [{module.status}] — {module.responsibility} (from {module.source_hint})'
            for module in self.modules
        ]


@lru_cache(maxsize=1)
def load_tools_snapshot() -> tuple[PortingModule, ...]:
    """Load the tools snapshot from parity.
    
    Returns:
        Tuple of PortingModule for all tools
    """
    if not SNAPSHOT_TOOLS_PATH.exists():
        return ()
    
    raw_entries = json.loads(SNAPSHOT_TOOLS_PATH.read_text(encoding="utf-8"))
    return tuple(
        PortingModule(
            name=entry["name"],
            responsibility=entry.get("responsibility", ""),
            source_hint=entry.get("source_hint", ""),
            status="mirrored",
        )
        for entry in raw_entries
    )


@lru_cache(maxsize=1)
def load_commands_snapshot() -> tuple[PortingModule, ...]:
    """Load the commands snapshot from parity.
    
    Returns:
        Tuple of PortingModule for all commands
    """
    if not SNAPSHOT_COMMANDS_PATH.exists():
        return ()
    
    raw_entries = json.loads(SNAPSHOT_COMMANDS_PATH.read_text(encoding="utf-8"))
    return tuple(
        PortingModule(
            name=entry["name"],
            responsibility=entry.get("responsibility", ""),
            source_hint=entry.get("source_hint", ""),
            status="mirrored",
        )
        for entry in raw_entries
    )


# Pre-loaded snapshots
PORTED_TOOLS = load_tools_snapshot()
PORTED_COMMANDS = load_commands_snapshot()


def build_tool_backlog() -> PortingBacklog:
    """Build the tool backlog.
    
    Returns:
        PortingBacklog with all tools
    """
    return PortingBacklog(title="Tool surface", modules=list(PORTED_TOOLS))


def build_command_backlog() -> PortingBacklog:
    """Build the command backlog.
    
    Returns:
        PortingBacklog with all commands
    """
    return PortingBacklog(title="Command surface", modules=list(PORTED_COMMANDS))


def get_tool_snapshot(name: str) -> Optional[PortingModule]:
    """Get a tool by name from the snapshot.
    
    Args:
        name: Tool name
        
    Returns:
        PortingModule or None if not found
    """
    needle = name.lower()
    for module in PORTED_TOOLS:
        if module.name.lower() == needle:
            return module
    return None


def get_command_snapshot(name: str) -> Optional[PortingModule]:
    """Get a command by name from the snapshot.
    
    Args:
        name: Command name
        
    Returns:
        PortingModule or None if not found
    """
    needle = name.lower()
    for module in PORTED_COMMANDS:
        if module.name.lower() == needle:
            return module
    return None


def find_tools(query: str, limit: int = 20) -> list[PortingModule]:
    """Find tools matching a query.
    
    Args:
        query: Search query
        limit: Maximum results
        
    Returns:
        List of matching tools
    """
    needle = query.lower()
    matches = [
        module for module in PORTED_TOOLS
        if needle in module.name.lower() or needle in module.responsibility.lower()
    ]
    return matches[:limit]


def find_commands(query: str, limit: int = 20) -> list[PortingModule]:
    """Find commands matching a query.
    
    Args:
        query: Search query
        limit: Maximum results
        
    Returns:
        List of matching commands
    """
    needle = query.lower()
    matches = [
        module for module in PORTED_COMMANDS
        if needle in module.name.lower() or needle in module.responsibility.lower()
    ]
    return matches[:limit]


def get_all_tool_names() -> list[str]:
    """Get all tool names from snapshot.
    
    Returns:
        List of tool names
    """
    return [module.name for module in PORTED_TOOLS]


def get_all_command_names() -> list[str]:
    """Get all command names from snapshot.
    
    Returns:
        List of command names
    """
    return [module.name for module in PORTED_COMMANDS]


__all__ = [
    "PortingModule",
    "PortingBacklog",
    "PORTED_TOOLS",
    "PORTED_COMMANDS",
    "load_tools_snapshot",
    "load_commands_snapshot",
    "build_tool_backlog",
    "build_command_backlog",
    "get_tool_snapshot",
    "get_command_snapshot",
    "find_tools",
    "find_commands",
    "get_all_tool_names",
    "get_all_command_names",
]
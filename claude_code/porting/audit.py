"""
Claude Code Python - Parity Audit

Provides functionality to audit parity between the Python implementation
and the TypeScript reference snapshots.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from claude_code.porting.snapshots import (
    PORTED_TOOLS,
    PORTED_COMMANDS,
    _PARITY_ROOT,
)


# Path to our implementation
OUR_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True, slots=True)
class ParityAuditResult:
    """Result of a parity audit between Python and TypeScript.
    
    Attributes:
        total_reference_tools: Total tools in TS reference
        total_implemented_tools: Tools we've implemented
        total_reference_commands: Total commands in TS reference
        total_implemented_commands: Commands we've implemented
        missing_tools: Tools from TS not yet implemented
        missing_commands: Commands from TS not yet implemented
    """
    total_reference_tools: int
    total_implemented_tools: int
    total_reference_commands: int
    total_implemented_commands: int
    missing_tools: tuple[str, ...] = field(default_factory=tuple)
    missing_commands: tuple[str, ...] = field(default_factory=tuple)

    @property
    def tool_coverage_percent(self) -> float:
        """Calculate tool coverage percentage."""
        if self.total_reference_tools == 0:
            return 0.0
        return (self.total_implemented_tools / self.total_reference_tools) * 100

    @property
    def command_coverage_percent(self) -> float:
        """Calculate command coverage percentage."""
        if self.total_reference_commands == 0:
            return 0.0
        return (self.total_implemented_commands / self.total_reference_commands) * 100

    def to_markdown(self) -> str:
        """Convert to markdown format."""
        lines = [
            "# Parity Audit Results",
            "",
            "## Tools",
            f"- Reference (TS): **{self.total_reference_tools}**",
            f"- Implemented (Python): **{self.total_implemented_tools}**",
            f"- Coverage: **{self.tool_coverage_percent:.1f}%**",
            "",
        ]
        
        if self.missing_tools:
            lines.append("### Missing Tools")
            for tool in self.missing_tools[:20]:
                lines.append(f"- {tool}")
            if len(self.missing_tools) > 20:
                lines.append(f"- ... and {len(self.missing_tools) - 20} more")
            lines.append("")
        
        lines.extend([
            "## Commands",
            f"- Reference (TS): **{self.total_reference_commands}**",
            f"- Implemented (Python): **{self.total_implemented_commands}**",
            f"- Coverage: **{self.command_coverage_percent:.1f}%**",
            "",
        ])
        
        if self.missing_commands:
            lines.append("### Missing Commands")
            for cmd in self.missing_commands[:20]:
                lines.append(f"- {cmd}")
            if len(self.missing_commands) > 20:
                lines.append(f"- ... and {len(self.missing_commands) - 20} more")
        
        return "\n".join(lines)


def run_parity_audit() -> ParityAuditResult:
    """Run a parity audit.
    
    Returns:
        ParityAuditResult with coverage information
    """
    from claude_code.tools import create_default_registry
    from claude_code.commands import get_all_commands
    
    # Get our implemented tools and commands
    our_registry = create_default_registry()
    our_tool_names = {t.name.lower() for t in our_registry.list_all()}
    our_command_names = set(get_all_commands().keys())
    
    # Get reference tool names
    reference_tool_names = {t.name.lower() for t in PORTED_TOOLS}
    
    # Get reference command names (handle duplicates)
    reference_command_names = set()
    for cmd in PORTED_COMMANDS:
        reference_command_names.add(cmd.name.lower())
    
    # Find missing
    missing_tools = sorted(reference_tool_names - our_tool_names)
    missing_commands = sorted(reference_command_names - our_command_names)
    
    return ParityAuditResult(
        total_reference_tools=len(PORTED_TOOLS),
        total_implemented_tools=len(our_tool_names),
        total_reference_commands=len(PORTED_COMMANDS),
        total_implemented_commands=len(our_command_names),
        missing_tools=tuple(missing_tools),
        missing_commands=tuple(missing_commands),
    )


__all__ = [
    "ParityAuditResult",
    "run_parity_audit",
]
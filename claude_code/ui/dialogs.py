"""
Claude Code Python - Dialog Launchers

Provides dialog launching capabilities for various views.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DialogLauncher:
    """A dialog launcher for launching various views.
    
    Attributes:
        name: Dialog name/identifier
        description: Human-readable description
    """
    name: str
    description: str

    def as_dict(self) -> dict[str, str]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "name": self.name,
            "description": self.description,
        }

    def as_markdown(self) -> str:
        """Convert to markdown format.
        
        Returns:
            Markdown formatted string
        """
        return f"- **{self.name}**: {self.description}"


# Default dialog launchers
DEFAULT_DIALOGS: tuple[DialogLauncher, ...] = (
    DialogLauncher("summary", "Launch the Markdown summary view"),
    DialogLauncher("parity_audit", "Launch the parity audit view"),
    DialogLauncher("tool_index", "Launch the tool index view"),
    DialogLauncher("command_index", "Launch the command index view"),
    DialogLauncher("setup_report", "Launch the setup report view"),
    DialogLauncher("bootstrap_graph", "Launch the bootstrap graph view"),
)


def get_dialog(name: str) -> Optional[DialogLauncher]:
    """Get a dialog launcher by name.
    
    Args:
        name: Dialog name
        
    Returns:
        DialogLauncher or None if not found
    """
    for dialog in DEFAULT_DIALOGS:
        if dialog.name == name:
            return dialog
    return None


def list_dialogs() -> list[str]:
    """List all available dialog names.
    
    Returns:
        List of dialog names
    """
    return [dialog.name for dialog in DEFAULT_DIALOGS]


def get_all_dialogs() -> tuple[DialogLauncher, ...]:
    """Get all default dialogs.
    
    Returns:
        Tuple of all DialogLaunchers
    """
    return DEFAULT_DIALOGS


def launch_dialog(name: str) -> str:
    """Launch a dialog and return status.
    
    Args:
        name: Dialog name
        
    Returns:
        Status message
    """
    dialog = get_dialog(name)
    if dialog:
        return f"Launching dialog: {dialog.name} - {dialog.description}"
    return f"Unknown dialog: {name}"


def as_dialog_menu() -> str:
    """Get all dialogs as a menu format.
    
    Returns:
        Menu formatted string
    """
    lines = ["Available Dialogs:", ""]
    for dialog in DEFAULT_DIALOGS:
        lines.append(dialog.as_markdown())
    return "\n".join(lines)


__all__ = [
    "DialogLauncher",
    "DEFAULT_DIALOGS",
    "get_dialog",
    "list_dialogs",
    "get_all_dialogs",
    "launch_dialog",
    "as_dialog_menu",
]
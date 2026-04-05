"""
Panel components for Claude Code Python.

Provides panel-based UI elements.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Dataclass patterns (frozen/slots)
- Optional rich library support with graceful fallback
"""

from __future__ import annotations

from typing import Optional, Any
from dataclasses import dataclass


try:
    from rich.console import Console
    from rich.panel import Panel as RichPanel
    from rich.box import Box, ROUNDED
    RICH_AVAILABLE: bool = True
except ImportError:
    RICH_AVAILABLE = False
    RichPanel = None
    Box = None


# Default styling constants
_DEFAULT_BORDER_STYLE: str = "blue"
_DEFAULT_TITLE_COLOR: str = "cyan"


@dataclass(frozen=True, slots=True)
class PanelStyle:
    """Panel styling options.
    
    Using frozen=True, slots=True for immutability and memory efficiency.
    
    Attributes:
        border_style: Color/style for the panel border
        title_color: Color for the panel title
        box: Box style for panel borders
    """
    border_style: str = _DEFAULT_BORDER_STYLE
    title_color: str = _DEFAULT_TITLE_COLOR
    box: Any = ROUNDED


class Panel:
    """A panel component for displaying content.
    
    Wraps content in a bordered box. Falls back to simple
    ASCII rendering if rich is not available.
    
    Attributes:
        content: Content to display in the panel
        title: Optional title for the panel
        style: Panel styling options
    
    Example:
        >>> panel = Panel("Hello World", title="Greeting")
        >>> print(panel.render())
    """
    
    def __init__(
        self,
        content: str,
        title: Optional[str] = None,
        style: Optional[PanelStyle] = None,
    ):
        self.content = content
        self.title = title
        self.style = style or PanelStyle()
    
    def render(self, console: Optional[Any] = None) -> str:
        """Render the panel to a string.
        
        Args:
            console: Optional rich Console for rich output
            
        Returns:
            Panel string (empty if console provided), or fallback ASCII.
        """
        if RICH_AVAILABLE and RichPanel:
            if console:
                panel = RichPanel(
                    self.content,
                    title=self.title,
                    border_style=self.style.border_style,
                    box=self.style.box,
                )
                console.print(panel)
            return ""
        else:
            lines: list[str] = []
            if self.title:
                lines.append(f"=== {self.title} ===")
            lines.append(self.content)
            if self.title:
                lines.append("=" * (len(self.title) + 6))
            return "\n".join(lines)
    
    def __str__(self) -> str:
        """Return string representation of the panel."""
        return self.render()


class CollapsiblePanel(Panel):
    """A collapsible panel.
    
    Can be expanded or collapsed. When collapsed, shows
    a marker and placeholder content.
    
    Attributes:
        collapsed: Whether the panel is currently collapsed
    """
    
    def __init__(
        self,
        content: str,
        title: Optional[str] = None,
        collapsed: bool = False,
        style: Optional[PanelStyle] = None,
    ):
        super().__init__(content, title, style)
        self._collapsed = collapsed
    
    @property
    def collapsed(self) -> bool:
        """Get the collapsed state."""
        return self._collapsed
    
    @collapsed.setter
    def collapsed(self, value: bool) -> None:
        """Set the collapsed state."""
        self._collapsed = value
    
    def toggle(self) -> None:
        """Toggle the collapsed state."""
        self._collapsed = not self._collapsed
    
    def expand(self) -> None:
        """Expand the panel."""
        self._collapsed = False
    
    def collapse(self) -> None:
        """Collapse the panel."""
        self._collapsed = True
    
    def render(self, console: Optional[Any] = None) -> str:
        """Render the panel, respecting collapsed state.
        
        Args:
            console: Optional rich Console for rich output
            
        Returns:
            Panel string with collapsed or expanded content.
        """
        if self._collapsed:
            marker = "[+]"
        else:
            marker = "[-]"
        
        if self.title:
            header = f"{marker} {self.title}"
        else:
            header = marker
        
        if self._collapsed:
            content = "(click to expand)"
        else:
            content = self.content
        
        if RICH_AVAILABLE and RichPanel:
            if console:
                panel = RichPanel(
                    content,
                    title=header,
                    border_style=self.style.border_style,
                    box=self.style.box,
                )
                console.print(panel)
            return ""
        else:
            lines = [header]
            if not self._collapsed:
                lines.append(content)
            return "\n".join(lines)


class InfoPanel(Panel):
    """An info panel with blue styling.
    
    Useful for displaying informational messages.
    """
    
    def __init__(self, content: str, title: Optional[str] = None):
        super().__init__(
            content,
            title=title,
            style=PanelStyle(border_style="blue", title_color="blue"),
        )


class WarningPanel(Panel):
    """A warning panel with yellow styling.
    
    Useful for displaying warning messages.
    """
    
    def __init__(self, content: str, title: Optional[str] = None):
        super().__init__(
            content,
            title=title or "Warning",
            style=PanelStyle(border_style="yellow", title_color="yellow"),
        )


class ErrorPanel(Panel):
    """An error panel with red styling.
    
    Useful for displaying error messages.
    """
    
    def __init__(self, content: str, title: Optional[str] = None):
        super().__init__(
            content,
            title=title or "Error",
            style=PanelStyle(border_style="red", title_color="red"),
        )


class SuccessPanel(Panel):
    """A success panel with green styling.
    
    Useful for displaying success/confirmation messages.
    """
    
    def __init__(self, content: str, title: Optional[str] = None):
        super().__init__(
            content,
            title=title or "Success",
            style=PanelStyle(border_style="green", title_color="green"),
        )


def create_panel(
    content: str,
    title: Optional[str] = None,
    panel_type: str = "default",
) -> Panel:
    """Create a panel of the specified type.
    
    Args:
        content: Content to display
        title: Optional title
        panel_type: Type ("default", "info", "warning", "error", "success")
        
    Returns:
        A Panel subclass instance.
    """
    if panel_type == "info":
        return InfoPanel(content, title)
    elif panel_type == "warning":
        return WarningPanel(content, title)
    elif panel_type == "error":
        return ErrorPanel(content, title)
    elif panel_type == "success":
        return SuccessPanel(content, title)
    else:
        return Panel(content, title)

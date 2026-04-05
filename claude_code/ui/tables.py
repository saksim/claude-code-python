"""
Table components for Claude Code Python.

Provides table formatting for displaying data.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Optional rich library support with graceful fallback
"""

from __future__ import annotations

from typing import Optional, Any


try:
    from rich.console import Console
    from rich.table import Table as RichTable
    from rich.box import Box, ROUNDED
    RICH_AVAILABLE: bool = True
except ImportError:
    RICH_AVAILABLE = False
    RichTable = None
    Box = None


class Table:
    """A table component.
    
    Displays data in a tabular format. Falls back to simple ASCII
    rendering if the rich library is not available.
    
    Attributes:
        headers: Column headers
        rows: Data rows
        title: Optional table title
        style: Current style name
    
    Example:
        >>> table = Table(["Name", "Age"], [["Alice", "30"], ["Bob", "25"]])
        >>> print(table.render())
    """
    
    def __init__(
        self,
        headers: list[str],
        rows: list[list[str]],
        title: Optional[str] = None,
    ):
        self.headers = headers
        self.rows = rows
        self.title = title
        self._style = "default"
    
    def set_style(self, style: str) -> None:
        """Set the table style.
        
        Args:
            style: Style name (currently unused, reserved for future).
        """
        self._style = style
    
    def render(self, console: Optional[Any] = None) -> str:
        """Render the table to a string.
        
        Args:
            console: Optional rich Console for rich output
            
        Returns:
            Table string (empty if console provided), or fallback ASCII table.
        """
        if RICH_AVAILABLE and RichTable:
            table = RichTable(title=self.title, show_header=True)
            
            for header in self.headers:
                table.add_column(header)
            
            for row in self.rows:
                table.add_row(*[str(cell) for cell in row])
            
            if console:
                console.print(table)
            return ""
        else:
            lines: list[str] = []
            if self.title:
                lines.append(f"=== {self.title} ===")
            
            header_line = " | ".join(self.headers)
            lines.append(header_line)
            lines.append("-" * len(header_line))
            
            for row in self.rows:
                lines.append(" | ".join(str(cell) for cell in row))
            
            return "\n".join(lines)
    
    def __str__(self) -> str:
        """Return string representation of the table."""
        return self.render()


def create_table(
    headers: list[str],
    rows: list[list[str]],
    title: Optional[str] = None,
) -> Table:
    """Create a table.
    
    Args:
        headers: Column headers
        rows: Data rows
        title: Optional table title
        
    Returns:
        A new Table instance.
    """
    return Table(headers, rows, title)


def format_key_value_table(
    data: dict[str, Any],
    title: Optional[str] = None,
) -> str:
    """Format a dictionary as a key-value table.
    
    Args:
        data: Dictionary to format
        title: Optional table title
        
    Returns:
        Formatted table string.
    """
    rows = [[k, str(v)] for k, v in data.items()]
    table = create_table(["Key", "Value"], rows, title)
    return str(table)


def format_list_table(
    items: list[str],
    title: Optional[str] = None,
) -> str:
    """Format a list as a table with numbers.
    
    Args:
        items: List of items to format
        title: Optional table title
        
    Returns:
        Formatted table string.
    """
    rows = [[str(i + 1), item] for i, item in enumerate(items)]
    table = create_table(["#", "Item"], rows, title)
    return str(table)


def format_tree_table(
    data: list[dict[str, Any]],
    name_key: str = "name",
    children_key: str = "children",
    indent: int = 2,
) -> str:
    """Format hierarchical data as an indented tree.
    
    Args:
        data: List of node dictionaries
        name_key: Key for node name
        children_key: Key for child nodes
        indent: Spaces per indent level
        
    Returns:
        Tree-formatted string.
    """
    lines: list[str] = []
    
    def render_node(node: dict[str, Any], prefix: str = "", is_last: bool = True) -> None:
        name = node.get(name_key, "")
        
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{name}")
        
        children = node.get(children_key, [])
        child_prefix = prefix + ("    " if is_last else "│   ")
        
        for i, child in enumerate(children):
            is_last_child = i == len(children) - 1
            render_node(child, child_prefix, is_last_child)
    
    for i, item in enumerate(data):
        is_last = i == len(data) - 1
        render_node(item, "", is_last)
    
    return "\n".join(lines)

"""
Claude Code Python - Bootstrap Context

Provides workspace context for bootstrap.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class PortContext:
    """Workspace context information.
    
    Attributes:
        source_root: Path to source code
        tests_root: Path to tests
        assets_root: Path to assets
        archive_root: Path to TS archive (if available)
        python_file_count: Number of Python files
        test_file_count: Number of test files
        asset_file_count: Number of asset files
        archive_available: Whether archive is available
    """
    source_root: Path
    tests_root: Path
    assets_root: Path
    archive_root: Path
    python_file_count: int
    test_file_count: int
    asset_file_count: int
    archive_available: bool


def build_port_context(base: Path | None = None) -> PortContext:
    """Build the workspace port context.
    
    Args:
        base: Base directory (defaults to current directory)
        
    Returns:
        PortContext instance
    """
    root = base or Path.cwd()
    source_root = root / "src"
    tests_root = root / "tests"
    assets_root = root / "assets"
    archive_root = root / "archive" / "claude_code_ts_snapshot" / "src"
    
    return PortContext(
        source_root=source_root,
        tests_root=tests_root,
        assets_root=assets_root,
        archive_root=archive_root,
        python_file_count=sum(1 for path in source_root.rglob("*.py") if path.is_file()) if source_root.exists() else 0,
        test_file_count=sum(1 for path in tests_root.rglob("*.py") if path.is_file()) if tests_root.exists() else 0,
        asset_file_count=sum(1 for path in assets_root.rglob("*") if path.is_file()) if assets_root.exists() else 0,
        archive_available=archive_root.exists(),
    )


def render_context(context: PortContext) -> str:
    """Render context as text.
    
    Args:
        context: PortContext to render
        
    Returns:
        Rendered context string
    """
    return "\n".join([
        f"Source root: {context.source_root}",
        f"Test root: {context.tests_root}",
        f"Assets root: {context.assets_root}",
        f"Archive root: {context.archive_root}",
        f"Python files: {context.python_file_count}",
        f"Test files: {context.test_file_count}",
        f"Assets: {context.asset_file_count}",
        f"Archive available: {context.archive_available}",
    ])


__all__ = [
    "PortContext",
    "build_port_context",
    "render_context",
]
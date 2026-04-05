"""
Claude Code Python - Setup System

Provides workspace setup and startup reporting.
"""

from __future__ import annotations

import sys
import platform
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime


@dataclass(frozen=True)
class PrefetchResult:
    """Result of a prefetch operation.
    
    Attributes:
        name: Prefetch operation name
        started: Whether it started successfully
        detail: Details about the prefetch
    """
    name: str
    started: bool
    detail: str


@dataclass(frozen=True)
class DeferredInitResult:
    """Result of deferred initialization.
    
    Attributes:
        trusted: Whether running in trusted mode
        plugin_init: Whether plugin init is enabled
        skill_init: Whether skill init is enabled
        mcp_prefetch: Whether MCP prefetch is enabled
        session_hooks: Whether session hooks are enabled
    """
    trusted: bool
    plugin_init: bool
    skill_init: bool
    mcp_prefetch: bool
    session_hooks: bool

    def as_lines(self) -> tuple[str, ...]:
        """Get initialization lines."""
        return (
            f"- trusted={self.trusted}",
            f"- plugin_init={self.plugin_init}",
            f"- skill_init={self.skill_init}",
            f"- mcp_prefetch={self.mcp_prefetch}",
            f"- session_hooks={self.session_hooks}",
        )


@dataclass(frozen=True)
class WorkspaceSetup:
    """Workspace setup information.
    
    Attributes:
        python_version: Python version string
        implementation: Python implementation (CPython, PyPy, etc.)
        platform_name: Platform name
        test_command: Default test command
    """
    python_version: str
    implementation: str
    platform_name: str
    test_command: str = "python -m pytest"

    def startup_steps(self) -> tuple[str, ...]:
        """Get startup steps."""
        return (
            "start top-level prefetch side effects",
            "build workspace context",
            "load mirrored command snapshot",
            "load mirrored tool snapshot",
            "prepare parity audit hooks",
            "apply trust-gated deferred init",
        )


@dataclass
class SetupReport:
    """Complete setup report.
    
    Attributes:
        setup: Workspace setup information
        prefetches: Tuple of prefetch results
        deferred_init: Deferred initialization result
        trusted: Whether running in trusted mode
        cwd: Current working directory
        created_at: When the report was created
    """
    setup: WorkspaceSetup
    prefetches: tuple[PrefetchResult, ...] = field(default_factory=tuple)
    deferred_init: DeferredInitResult = None
    trusted: bool = True
    cwd: Path = field(default_factory=Path.cwd)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        if self.deferred_init is None:
            object.__setattr__(self, 'deferred_init', run_deferred_init(self.trusted))

    def as_markdown(self) -> str:
        """Convert to markdown format."""
        prefetch_lines = [f"- {p.name}: {p.detail}" for p in self.prefetches] if self.prefetches else ["- none"]
        
        lines = [
            "# Setup Report",
            "",
            f"- Python: {self.setup.python_version} ({self.setup.implementation})",
            f"- Platform: {self.setup.platform_name}",
            f"- Trusted mode: {self.trusted}",
            f"- CWD: {self.cwd}",
            f"- Created: {self.created_at}",
            "",
            "Prefetches:",
            *prefetch_lines,
            "",
            "Deferred init:",
            *self.deferred_init.as_lines(),
        ]
        return "\n".join(lines)


def build_workspace_setup() -> WorkspaceSetup:
    """Build workspace setup information.
    
    Returns:
        WorkspaceSetup instance
    """
    return WorkspaceSetup(
        python_version=".".join(str(part) for part in sys.version_info[:3]),
        implementation=platform.python_implementation(),
        platform_name=platform.platform(),
    )


def run_deferred_init(trusted: bool = True) -> DeferredInitResult:
    """Run deferred initialization.
    
    Args:
        trusted: Whether running in trusted mode
        
    Returns:
        DeferredInitResult instance
    """
    enabled = bool(trusted)
    return DeferredInitResult(
        trusted=trusted,
        plugin_init=enabled,
        skill_init=enabled,
        mcp_prefetch=enabled,
        session_hooks=enabled,
    )


def start_mdm_raw_read() -> PrefetchResult:
    """Start MDM raw-read prefetch."""
    return PrefetchResult("mdm_raw_read", True, "Simulated MDM raw-read prefetch for workspace bootstrap")


def start_keychain_prefetch() -> PrefetchResult:
    """Start keychain prefetch."""
    return PrefetchResult("keychain_prefetch", True, "Simulated keychain prefetch for trusted startup path")


def start_project_scan(root: Path) -> PrefetchResult:
    """Start project scan prefetch."""
    return PrefetchResult("project_scan", True, f"Scanned project root {root}")


def run_setup(cwd: Path | None = None, trusted: bool = True) -> SetupReport:
    """Run workspace setup.
    
    Args:
        cwd: Current working directory
        trusted: Whether running in trusted mode
        
    Returns:
        SetupReport instance
    """
    root = cwd or Path.cwd()
    prefetches = (
        start_mdm_raw_read(),
        start_keychain_prefetch(),
        start_project_scan(root),
    )
    return SetupReport(
        setup=build_workspace_setup(),
        prefetches=prefetches,
        deferred_init=run_deferred_init(trusted),
        trusted=trusted,
        cwd=root,
    )


__all__ = [
    "PrefetchResult",
    "DeferredInitResult",
    "WorkspaceSetup",
    "SetupReport",
    "build_workspace_setup",
    "run_deferred_init",
    "start_mdm_raw_read",
    "start_keychain_prefetch",
    "start_project_scan",
    "run_setup",
]
"""
Claude Code Python - Project Onboarding State

Provides project onboarding state tracking.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProjectOnboardingState:
    """Project onboarding state.
    
    Attributes:
        has_readme: Whether project has README
        has_tests: Whether project has tests
        python_first: Whether Python is the primary language
    """
    has_readme: bool = False
    has_tests: bool = False
    python_first: bool = True

    def as_dict(self) -> dict[str, bool]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "has_readme": self.has_readme,
            "has_tests": self.has_tests,
            "python_first": self.python_first,
        }

    def as_markdown(self) -> str:
        """Convert to markdown format.
        
        Returns:
            Markdown formatted string
        """
        lines = ["# Project Onboarding State", ""]
        lines.append(f"- README: {'Yes' if self.has_readme else 'No'}")
        lines.append(f"- Tests: {'Yes' if self.has_tests else 'No'}")
        lines.append(f"- Primary Language: {'Python' if self.python_first else 'Other'}")
        return "\n".join(lines)


def detect_onboarding_state(project_root: Path | None = None) -> ProjectOnboardingState:
    """Detect project onboarding state.
    
    Args:
        project_root: Project root directory
        
    Returns:
        ProjectOnboardingState with detected values
    """
    root = project_root or Path.cwd()
    
    # Check for README files
    has_readme = (
        (root / "README.md").exists() or
        (root / "README.rst").exists() or
        (root / "README").exists()
    )
    
    # Check for tests directory/files
    has_tests = (
        (root / "tests").exists() or
        (root / "test").exists() or
        (root / "pytest.ini").exists() or
        (root / "setup.cfg").exists()
    )
    
    # Check for Python files (simple heuristic)
    python_files = list(root.glob("*.py"))
    python_first = len(python_files) > 0
    
    return ProjectOnboardingState(
        has_readme=has_readme,
        has_tests=has_tests,
        python_first=python_first,
    )


__all__ = [
    "ProjectOnboardingState",
    "detect_onboarding_state",
]
"""Context Builder for Claude Code Python.

Builds context for API requests including git status, CLAUDE.md, etc.
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ContextParts:
    """Parts of the context to include in system prompt.

    Attributes:
        system_context: System-level context dictionary.
        user_context: User-level context dictionary.
    """

    system_context: dict[str, Any]
    user_context: dict[str, Any]


class GitInfo:
    """Git repository information.

    Provides lazy-loaded git repository metadata with caching.
    """

    def __init__(self, working_dir: str | Path) -> None:
        """Initialize GitInfo.

        Args:
            working_dir: Working directory for git operations.
        """
        self._working_dir = Path(working_dir)
        self._is_git: bool | None = None
        self._branch: str | None = None
        self._default_branch: str | None = None
        self._status: str | None = None
        self._recent_commits: str | None = None
        self._user_name: str | None = None

    def is_git_repo(self) -> bool:
        """Check if directory is a git repository.

        Returns:
            True if the working directory is a git repository.
        """
        if self._is_git is None:
            try:
                result = subprocess.run(
                    ["git", "rev-parse", "--is-inside-work-tree"],
                    cwd=str(self._working_dir),
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                self._is_git = result.returncode == 0 and "true" in result.stdout
            except Exception:
                self._is_git = False
        return self._is_git

    def get_branch(self) -> str | None:
        """Get current branch name.

        Returns:
            Current branch name, or None if not in a git repo.
        """
        if not self.is_git_repo():
            return None

        if self._branch is None:
            try:
                result = subprocess.run(
                    ["git", "branch", "--show-current"],
                    cwd=str(self._working_dir),
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                self._branch = result.stdout.strip() if result.returncode == 0 else None
            except Exception:
                self._branch = None

        return self._branch

    def get_default_branch(self) -> str | None:
        """Get default branch name (main/master).

        Returns:
            Name of the default branch, or None if not in a git repo.
        """
        if not self.is_git_repo():
            return None

        if self._default_branch is None:
            try:
                result = subprocess.run(
                    ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
                    cwd=str(self._working_dir),
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    ref = result.stdout.strip()
                    self._default_branch = ref.replace("refs/remotes/origin/", "").strip()
                else:
                    self._default_branch = "main"
            except Exception:
                self._default_branch = "main"

        return self._default_branch

    def get_status(self) -> str | None:
        """Get git status output.

        Returns:
            Short-form git status, or None if not in a git repo.
        """
        if not self.is_git_repo():
            return None

        if self._status is None:
            try:
                result = subprocess.run(
                    ["git", "status", "--short"],
                    cwd=str(self._working_dir),
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                self._status = result.stdout.strip() if result.returncode == 0 else None
            except Exception:
                self._status = None

        return self._status

    def get_recent_commits(self, count: int = 5) -> str | None:
        """Get recent commits.

        Args:
            count: Number of commits to retrieve.

        Returns:
            Recent commits as formatted string, or None.
        """
        if not self.is_git_repo():
            return None

        if self._recent_commits is None:
            try:
                result = subprocess.run(
                    ["git", "log", f"-{count}", "--oneline"],
                    cwd=str(self._working_dir),
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                self._recent_commits = result.stdout.strip() if result.returncode == 0 else None
            except Exception:
                self._recent_commits = None

        return self._recent_commits

    def get_user_name(self) -> str | None:
        """Get configured git user name.

        Returns:
            Git user name, or None if not configured.
        """
        if not self.is_git_repo():
            return None

        if self._user_name is None:
            try:
                result = subprocess.run(
                    ["git", "config", "user.name"],
                    cwd=str(self._working_dir),
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                self._user_name = result.stdout.strip() if result.returncode == 0 else None
            except Exception:
                self._user_name = None

        return self._user_name

    def format_status(self) -> str | None:
        """Format git status for context.

        Returns:
            Formatted git status string, or None if not in a git repo.
        """
        if not self.is_git_repo():
            return None

        parts = [
            "This is the git status at the start of the conversation.",
            "Note that this status is a snapshot in time, and will not update during the conversation.",
            f"Current branch: {self.get_branch()}",
            f"Main branch: {self.get_default_branch()}",
        ]

        user_name = self.get_user_name()
        if user_name:
            parts.append(f"Git user: {user_name}")

        status = self.get_status()
        parts.append(f"Status:\n{status if status else '(clean)'}")

        commits = self.get_recent_commits()
        if commits:
            parts.append(f"Recent commits:\n{commits}")

        return "\n\n".join(parts)


class ClaudeMdLoader:
    """Load CLAUDE.md files from project hierarchy.

    Searches upward from the working directory to find all CLAUDE.md files.
    """

    def __init__(self, working_dir: str | Path) -> None:
        """Initialize ClaudeMdLoader.

        Args:
            working_dir: Working directory to search from.
        """
        self._working_dir = Path(working_dir)
        self._claude_md_cache: str | None = None

    def find_claude_md_files(self) -> list[Path]:
        """Find all CLAUDE.md files in directory hierarchy.

        Returns:
            List of Paths to CLAUDE.md files, ordered from root to current.
        """
        files: list[Path] = []

        current = self._working_dir
        while True:
            md_path = current / "CLAUDE.md"
            if md_path.is_file():
                files.append(md_path)

            if current.parent == current:
                break
            current = current.parent

        files.reverse()
        return files

    def _display_path(self, filepath: Path) -> str:
        """Return display path relative to working dir when possible."""
        try:
            return str(filepath.relative_to(self._working_dir))
        except ValueError:
            return os.path.relpath(filepath, self._working_dir)

    def load_content(self) -> str | None:
        """Load combined CLAUDE.md content.

        Returns:
            Combined content from all CLAUDE.md files, or None if none found.
        """
        if self._claude_md_cache is not None:
            return self._claude_md_cache

        files = self.find_claude_md_files()
        if not files:
            self._claude_md_cache = None
            return None

        contents: list[str] = []
        for filepath in files:
            try:
                content = filepath.read_text(encoding="utf-8").strip()
                if content:
                    rel_path = self._display_path(filepath)
                    contents.append(f"# {rel_path}\n\n{content}")
            except (OSError, UnicodeError) as exc:
                logger.warning("Failed to load %s: %s", filepath, exc)
                continue

        if contents:
            self._claude_md_cache = "\n\n---\n\n".join(contents)
        else:
            self._claude_md_cache = None

        return self._claude_md_cache


class ContextBuilder:
    """Builds context information for API requests.

    Collects git status, CLAUDE.md files, and other contextual
    information to include in the system prompt.
    
    Uses caching to avoid redundant computation.
    """

    def __init__(self, working_dir: str | Path | None = None) -> None:
        """Initialize ContextBuilder.

        Args:
            working_dir: Working directory (defaults to current directory).
        """
        self._working_dir = Path(working_dir) if working_dir else Path.cwd()
        self.git_info = GitInfo(self._working_dir)
        self.claude_md = ClaudeMdLoader(self._working_dir)
        
        # Caches for performance optimization
        self._system_prompt_cache: list[str] | None = None
        self._system_prompt_cache_dir: Path | None = None
        self._current_date_cache: str | None = None
        self._current_date_cache_day: str | None = None

    @property
    def working_dir(self) -> Path:
        """Get the working directory."""
        return self._working_dir

    def get_current_date(self) -> str:
        """Get current date formatted for display.
        
        Cached for performance - only recomputed when date changes.

        Returns:
            Formatted date string (YYYY-MM-DD).
        """
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Use cached date if still valid
        if self._current_date_cache is not None and self._current_date_cache_day == today:
            return self._current_date_cache
        
        # Compute and cache
        self._current_date_cache_day = today
        self._current_date_cache = today
        return self._current_date_cache

    def get_system_context(self) -> dict[str, Any]:
        """Get system context that doesn't change per conversation.

        This includes git status and other project information.

        Returns:
            Dictionary containing system context.
        """
        context: dict[str, Any] = {}

        git_status = self.git_info.format_status()
        if git_status:
            context["gitStatus"] = git_status

        return context

    def get_user_context(self) -> dict[str, Any]:
        """Get user context that varies per conversation.

        This includes CLAUDE.md content and other user-specific info.

        Returns:
            Dictionary containing user context.
        """
        context: dict[str, Any] = {}

        claude_md_content = self.claude_md.load_content()
        if claude_md_content:
            context["claudeMd"] = claude_md_content

        context["currentDate"] = f"Today's date is {self.get_current_date()}."

        return context

    def build_system_prompt_parts(self) -> list[str]:
        """Build parts for system prompt.
        
        Cached based on working directory to avoid redundant computation.

        Returns:
            List of context strings to include in system prompt.
        """
        # Check cache validity
        if self._system_prompt_cache is not None:
            if self._system_prompt_cache_dir == self._working_dir:
                return self._system_prompt_cache
        
        # Compute and cache
        parts: list[str] = []

        git_context = self.get_system_context()
        if "gitStatus" in git_context:
            parts.append(git_context["gitStatus"])

        user_context = self.get_user_context()
        if "claudeMd" in user_context:
            parts.append(user_context["claudeMd"])
        if "currentDate" in user_context:
            parts.append(user_context["currentDate"])

        # Store in cache
        self._system_prompt_cache = parts
        self._system_prompt_cache_dir = self._working_dir
        
        return parts

    def invalidate_cache(self) -> None:
        """Invalidate cached context."""
        self.claude_md._claude_md_cache = None
        self.git_info._is_git = None
        self.git_info._branch = None
        self.git_info._status = None
        self.git_info._recent_commits = None
        
        # Invalidate computed caches
        self._system_prompt_cache = None
        self._system_prompt_cache_dir = None
        self._current_date_cache = None
        self._current_date_cache_day = None


# PermissionMode is imported from claude_code.permissions — canonical source
from claude_code.permissions import PermissionMode


@dataclass
class PermissionContext:
    """Context for permission decisions.

    Attributes:
        mode: Current permission mode.
        always_allow: List of patterns to always allow.
        always_deny: List of patterns to always deny.
    """

    mode: PermissionMode
    always_allow: list[str] = field(default_factory=list)
    always_deny: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Post-initialization processing."""
        if not self.always_allow:
            self.always_allow = []
        if not self.always_deny:
            self.always_deny = []

    def should_allow(self, tool_name: str, input_data: dict[str, Any]) -> bool:
        """Check if tool should be auto-allowed.

        Args:
            tool_name: Name of the tool.
            input_data: Input data for the tool.

        Returns:
            True if the tool should be allowed automatically.
        """
        if self.mode == PermissionMode.BYPASS:
            return True

        for pattern in self.always_allow:
            if self._matches_pattern(pattern, tool_name, input_data):
                return True

        for pattern in self.always_deny:
            if self._matches_pattern(pattern, tool_name, input_data):
                return False

        return False

    def _matches_pattern(
        self,
        pattern: str,
        tool_name: str,
        input_data: dict[str, Any],
    ) -> bool:
        """Check if input matches an allow/deny pattern.

        Args:
            pattern: Pattern to match against.
            tool_name: Name of the tool.
            input_data: Input data dictionary.

        Returns:
            True if the input matches the pattern.
        """
        parts = pattern.split(maxsplit=1)

        if len(parts) == 1:
            return tool_name == parts[0]

        tool_pattern, input_pattern = parts

        if tool_pattern not in ("*", tool_name):
            return False

        if input_pattern and input_pattern != "*":
            input_str = json.dumps(input_data)
            return bool(re.search(input_pattern, input_str))

        return True

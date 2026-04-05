"""
Context building for Claude Code Python.

Builds context for API requests including git status, CLAUDE.md, memory files, etc.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Dataclass patterns
- Separation of concerns
"""

from __future__ import annotations

import os
import subprocess
import glob
from typing import Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class GitContext:
    """Git repository context.
    
    Attributes:
        is_git_repo: Whether the directory is a git repository
        branch: Current branch name
        default_branch: Default branch (main/master)
        status: Git status output
        recent_commits: Recent commit history
        user_name: Git user name
        user_email: Git user email
    """
    is_git_repo: bool = False
    branch: Optional[str] = None
    default_branch: Optional[str] = None
    status: Optional[str] = None
    recent_commits: Optional[str] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None


@dataclass(frozen=True, slots=True)
class WorkspaceContext:
    """Workspace/project context.
    
    Attributes:
        root_dir: Root directory of the project
        project_name: Name of the project
        project_type: Type of project (python, javascript, rust, etc.)
        languages: List of programming languages used
        package_managers: List of package managers (pip, npm, cargo, etc.)
        has_tests: Whether the project has tests
        has_lint: Whether the project has linting configured
    """
    root_dir: str
    project_name: str
    project_type: Optional[str] = None
    languages: list[str] = field(default_factory=list)
    package_managers: list[str] = field(default_factory=list)
    has_tests: bool = False
    has_lint: bool = False


@dataclass(frozen=True, slots=True)
class MemoryContext:
    """Memory files context.
    
    Attributes:
        memory_files: List of memory file paths
        claude_md_files: List of CLAUDE.md file paths
    """
    memory_files: list[str] = field(default_factory=list)
    claude_md_files: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class SystemContext:
    """System context.
    
    Attributes:
        os: Operating system name
        hostname: Optional hostname
        cwd: Current working directory
        date: Current date/time
    """
    os: str
    cwd: str
    date: str
    hostname: Optional[str] = None


class ContextBuilder:
    """
    Builds comprehensive context for API requests.
    
    Collects git status, CLAUDE.md files, memory files, and other
    contextual information to provide to the Claude API.
    
    Following Python best practices:
    - Clear type hints
    - Comprehensive docstrings
    - Dataclass for immutable data
    - Modular design
    """
    
    def __init__(self, working_dir: Optional[str] = None):
        self.working_dir = working_dir or os.getcwd()
        self._git_context: Optional[GitContext] = None
        self._workspace_context: Optional[WorkspaceContext] = None
        self._memory_context: Optional[MemoryContext] = None
    
    def get_git_context(self, force_refresh: bool = False) -> GitContext:
        """Get git repository context."""
        if self._git_context is not None and not force_refresh:
            return self._git_context
        
        ctx = GitContext()
        
        if not self._is_git_repo():
            self._git_context = ctx
            return ctx
        
        ctx.is_git_repo = True
        
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                ctx.branch = result.stdout.strip()
        except:
            pass
        
        try:
            result = subprocess.run(
                ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                ctx.default_branch = result.stdout.strip().replace("refs/remotes/origin/", "")
            else:
                ctx.default_branch = "main"
        except:
            ctx.default_branch = "main"
        
        try:
            result = subprocess.run(
                ["git", "status", "--short"],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                ctx.status = result.stdout.strip()
        except:
            pass
        
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "-n", "5"],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                ctx.recent_commits = result.stdout.strip()
        except:
            pass
        
        try:
            result = subprocess.run(
                ["git", "config", "user.name"],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                ctx.user_name = result.stdout.strip()
        except:
            pass
        
        try:
            result = subprocess.run(
                ["git", "config", "user.email"],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                ctx.user_email = result.stdout.strip()
        except:
            pass
        
        self._git_context = ctx
        return ctx
    
    def get_workspace_context(self) -> WorkspaceContext:
        """Get workspace/project context."""
        if self._workspace_context is not None:
            return self._workspace_context
        
        ctx = WorkspaceContext(
            root_dir=self.working_dir,
            project_name=os.path.basename(self.working_dir),
        )
        
        # Detect project type from files
        project_files = {
            "python": ["setup.py", "pyproject.toml", "requirements.txt", "Pipfile"],
            "node": ["package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"],
            "rust": ["Cargo.toml", "Cargo.lock"],
            "go": ["go.mod", "go.sum"],
            "java": ["pom.xml", "build.gradle"],
            "dotnet": ["*.csproj", "*.sln"],
        }
        
        for ptype, files in project_files.items():
            for pattern in files:
                if glob.glob(os.path.join(self.working_dir, pattern)):
                    ctx.project_type = ptype
                    ctx.package_managers.append(ptype)
                    break
            if ctx.project_type:
                break
        
        # Detect languages
        for ext in [".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs"]:
            if glob.glob(os.path.join(self.working_dir, "**", f"*{ext}"), recursive=True):
                lang_map = {
                    ".py": "Python",
                    ".js": "JavaScript",
                    ".ts": "TypeScript",
                    ".jsx": "JavaScript (React)",
                    ".tsx": "TypeScript (React)",
                    ".java": "Java",
                    ".go": "Go",
                    ".rs": "Rust",
                }
                ctx.languages.append(lang_map.get(ext, ext[1:].title()))
        
        # Check for tests
        test_patterns = [
            "**/test_*.py",
            "**/*_test.py",
            "**/tests/**/*.py",
            "**/*.test.js",
            "**/*.test.ts",
            "**/__tests__/**/*.js",
        ]
        for pattern in test_patterns:
            if glob.glob(os.path.join(self.working_dir, pattern), recursive=True):
                ctx.has_tests = True
                break
        
        # Check for linting
        lint_files = [".eslintrc", ".prettierrc", "pyproject.toml", ".flake8", "ruff.toml"]
        for f in lint_files:
            if glob.glob(os.path.join(self.working_dir, f)):
                ctx.has_lint = True
                break
        
        self._workspace_context = ctx
        return ctx
    
    def get_memory_files(self) -> list[str]:
        """Get paths of memory files."""
        memory_files = []
        
        # Look for .claude/memory directories
        search_paths = [
            os.path.join(self.working_dir, ".claude", "memory"),
            os.path.expanduser("~/.claude/memory"),
        ]
        
        for search_path in search_paths:
            if os.path.isdir(search_path):
                for ext in ["*.md", "*.txt"]:
                    memory_files.extend(glob.glob(os.path.join(search_path, "**", ext), recursive=True))
        
        return memory_files
    
    def get_claude_md_files(self) -> list[str]:
        """Get paths of CLAUDE.md files."""
        files = []
        current = self.working_dir
        
        while current and current != "/":
            md_path = os.path.join(current, "CLAUDE.md")
            if os.path.isfile(md_path):
                files.append(md_path)
            
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent
        
        return files
    
    def format_git_context(self) -> Optional[str]:
        """Format git context as a string."""
        git = self.get_git_context()
        
        if not git.is_git_repo:
            return None
        
        parts = [
            "Git Status:",
            f"- Branch: {git.branch}",
            f"- Main branch: {git.default_branch}",
        ]
        
        if git.user_name:
            parts.append(f"- User: {git.user_name}")
        
        parts.append("- Status:")
        
        if git.status:
            status_lines = git.status.split('\n')[:20]
            parts.append("  " + "\n  ".join(status_lines))
            if len(git.status.split('\n')) > 20:
                parts.append("  ... (truncated)")
        else:
            parts.append("  (clean)")
        
        if git.recent_commits:
            parts.append("- Recent commits:")
            commits = git.recent_commits.split('\n')[:5]
            parts.append("  " + "\n  ".join(commits))
        
        return "\n".join(parts)
    
    def format_claude_md_context(self) -> Optional[str]:
        """Format CLAUDE.md content as a string."""
        files = self.get_claude_md_files()
        
        if not files:
            return None
        
        contents = []
        for filepath in files:
            try:
                rel_path = os.path.relpath(filepath, self.working_dir)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        contents.append(f"=== {rel_path} ===\n\n{content}")
            except:
                continue
        
        if not contents:
            return None
        
        return "\n\n---\n\n".join(contents)
    
    def format_workspace_context(self) -> Optional[str]:
        """Format workspace context as a string."""
        ws = self.get_workspace_context()
        
        if not ws.project_type:
            return None
        
        parts = [
            "Project Information:",
            f"- Type: {ws.project_type}",
        ]
        
        if ws.languages:
            parts.append(f"- Languages: {', '.join(ws.languages)}")
        
        if ws.package_managers:
            parts.append(f"- Package managers: {', '.join(ws.package_managers)}")
        
        if ws.has_tests:
            parts.append("- Has tests: Yes")
        
        if ws.has_lint:
            parts.append("- Has linting: Yes")
        
        return "\n".join(parts)
    
    def build_system_prompt_parts(self) -> list[str]:
        """Build all context parts for system prompt."""
        parts = []
        
        git_context = self.format_git_context()
        if git_context:
            parts.append(git_context)
        
        claude_md = self.format_claude_md_context()
        if claude_md:
            parts.append(claude_md)
        
        workspace = self.format_workspace_context()
        if workspace:
            parts.append(workspace)
        
        return parts
    
    def _is_git_repo(self) -> bool:
        """Check if directory is a git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0 and "true" in result.stdout
        except:
            return False
    
    def invalidate_cache(self) -> None:
        """Invalidate all cached context."""
        self._git_context = None
        self._workspace_context = None
        self._memory_context = None

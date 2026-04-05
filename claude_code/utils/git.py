"""
Git utilities for Claude Code Python.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Dataclass patterns
- Frozen for immutable configs
"""

from __future__ import annotations

import os
import subprocess
from typing import Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class GitStatus(Enum):
    """Git repository status.
    
    Attributes:
        CLEAN: No uncommitted changes
        DIRTY: Has uncommitted changes
        UNTRACKED: Has untracked files
    """
    CLEAN = "clean"
    DIRTY = "dirty"
    UNTRACKED = "untracked"


@dataclass(frozen=True, slots=True)
class GitInfo:
    """Git repository information.
    
    Immutable snapshot of repository state at a point in time.
    
    Attributes:
        is_repo: Whether path is inside a git repository
        branch: Current branch name
        commit: Current commit hash (short)
        status: Overall repository status
        has_changes: Whether there are uncommitted changes
        staged_files: List of staged file paths
        modified_files: List of modified (unstaged) file paths
        untracked_files: List of untracked file paths
    """
    is_repo: bool = False
    branch: Optional[str] = None
    commit: Optional[str] = None
    status: GitStatus = GitStatus.CLEAN
    has_changes: bool = False
    staged_files: list[str] = field(default_factory=list)
    modified_files: list[str] = field(default_factory=list)
    untracked_files: list[str] = field(default_factory=list)


def run_git_command(
    args: list[str],
    cwd: Optional[str] = None,
) -> tuple[int, str, str]:
    """Run a git command and return result.
    
    Args:
        args: Git command arguments (e.g., ["status", "-s"])
        cwd: Working directory for command
        
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            cwd=cwd or os.getcwd(),
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return -1, "", "Git not found"
    except OSError as e:
        return -1, "", str(e)


def is_git_repo(path: Optional[str] = None) -> bool:
    """Check if a path is inside a git repository.
    
    Args:
        path: Path to check (defaults to current directory)
        
    Returns:
        True if path is inside a git repository
    """
    _, stdout, _ = run_git_command(["rev-parse", "--is-inside-work-tree"], cwd=path)
    return stdout == "true"


def get_git_root(path: Optional[str] = None) -> Optional[str]:
    """Get the root of the git repository.
    
    Args:
        path: Path within the repository
        
    Returns:
        Root directory path, or None if not in a repo
    """
    returncode, stdout, _ = run_git_command(["rev-parse", "--show-toplevel"], cwd=path)
    if returncode == 0:
        return stdout
    return None


def get_current_branch(path: Optional[str] = None) -> Optional[str]:
    """Get the current branch name.
    
    Args:
        path: Path within the repository
        
    Returns:
        Current branch name, or None if not on a branch
    """
    returncode, stdout, _ = run_git_command(["branch", "--show-current"], cwd=path)
    if returncode == 0 and stdout:
        return stdout
    return None


def get_current_commit(path: Optional[str] = None, short: bool = True) -> Optional[str]:
    """Get the current commit hash.
    
    Args:
        path: Path within the repository
        short: Whether to return short hash
        
    Returns:
        Commit hash, or None if not in a repo
    """
    fmt = "%h" if short else "%H"
    returncode, stdout, _ = run_git_command(["rev-parse", fmt], cwd=path)
    if returncode == 0 and stdout:
        return stdout
    return None


def get_git_status(path: Optional[str] = None) -> GitInfo:
    """Get comprehensive git status information.
    
    Args:
        path: Path within the repository
        
    Returns:
        GitInfo with full repository status
    """
    info = GitInfo()
    
    if not is_git_repo(path):
        return info
    
    info = GitInfo(
        is_repo=True,
        branch=get_current_branch(path),
        commit=get_current_commit(path, short=True),
    )
    
    # Get porcelain status
    returncode, stdout, _ = run_git_command(
        ["status", "--porcelain=v1", "-uall"],
        cwd=path
    )
    
    if returncode == 0:
        staged: list[str] = []
        modified: list[str] = []
        untracked: list[str] = []
        
        for line in stdout.split('\n'):
            if not line:
                continue
            
            status = line[:2]
            filepath = line[3:]
            
            if status[0] in ('M', 'A', 'R', 'C'):
                staged.append(filepath)
                info.has_changes = True
            if status[1] in ('M', 'D'):
                modified.append(filepath)
                info.has_changes = True
            if status == '??':
                untracked.append(filepath)
                info.has_changes = True
        
        # Return new instance with updated lists
        return GitInfo(
            is_repo=True,
            branch=info.branch,
            commit=info.commit,
            status=GitStatus.DIRTY if info.has_changes else GitStatus.CLEAN,
            has_changes=info.has_changes,
            staged_files=staged,
            modified_files=modified,
            untracked_files=untracked,
        )
    
    return info


def get_diff(path: Optional[str] = None, staged: bool = False) -> str:
    """Get the git diff.
    
    Args:
        path: Path within the repository
        staged: Whether to show staged changes
        
    Returns:
        Diff output as string
    """
    args = ["diff"]
    if staged:
        args.append("--cached")
    
    _, stdout, _ = run_git_command(args, cwd=path)
    return stdout


def get_diff_stat(path: Optional[str] = None) -> str:
    """Get diff statistics.
    
    Args:
        path: Path within the repository
        
    Returns:
        Diff stat output
    """
    _, stdout, _ = run_git_command(["diff", "--stat"], cwd=path)
    return stdout


def get_stashes(path: Optional[str] = None) -> list[str]:
    """Get list of git stashes.
    
    Args:
        path: Path within the repository
        
    Returns:
        List of stash references
    """
    _, stdout, _ = run_git_command(["stash", "list"], cwd=path)
    return stdout.split('\n') if stdout else []


def get_branches(path: Optional[str] = None, remote: bool = False) -> list[str]:
    """Get list of branches.
    
    Args:
        path: Path within the repository
        remote: Whether to include remote branches
        
    Returns:
        List of branch names
    """
    args = ["branch", "-a" if remote else "-v"]
    returncode, stdout, _ = run_git_command(args, cwd=path)
    
    if returncode == 0:
        branches: list[str] = []
        for b in stdout.split('\n'):
            if not b.strip():
                continue
            if '->' in b:
                branches.append(b.split('->')[1].strip())
            else:
                branches.append(b.strip().split()[0])
        return branches
    return []


def create_branch(name: str, checkout: bool = True, path: Optional[str] = None) -> bool:
    """Create a new branch.
    
    Args:
        name: Branch name
        checkout: Whether to checkout the new branch
        path: Path within the repository
        
    Returns:
        True if successful
    """
    args = ["checkout", "-b", name] if checkout else ["branch", name]
    returncode, _, _ = run_git_command(args, cwd=path)
    return returncode == 0


def checkout_branch(branch: str, path: Optional[str] = None) -> bool:
    """Checkout a branch.
    
    Args:
        branch: Branch name to checkout
        path: Path within the repository
        
    Returns:
        True if successful
    """
    returncode, _, _ = run_git_command(["checkout", branch], cwd=path)
    return returncode == 0


def commit(message: str, path: Optional[str] = None) -> bool:
    """Create a commit.
    
    Args:
        message: Commit message
        path: Path within the repository
        
    Returns:
        True if successful
    """
    returncode, _, _ = run_git_command(["commit", "-m", message], cwd=path)
    return returncode == 0


def add(files: list[str], path: Optional[str] = None) -> bool:
    """Stage files for commit.
    
    Args:
        files: List of file paths to stage
        path: Path within the repository
        
    Returns:
        True if successful
    """
    returncode, _, _ = run_git_command(["add"] + files, cwd=path)
    return returncode == 0


def get_commit_history(count: int = 10, path: Optional[str] = None) -> list[dict[str, Any]]:
    """Get commit history.
    
    Args:
        count: Number of commits to retrieve
        path: Path within the repository
        
    Returns:
        List of commit dictionaries with hash, message, author, date
    """
    _, stdout, _ = run_git_command(
        ["log", f"-{count}", "--pretty=format:%H|%s|%an|%ad", "--date=iso"],
        cwd=path
    )
    
    commits: list[dict[str, Any]] = []
    for line in stdout.split('\n'):
        if not line:
            continue
        parts = line.split('|')
        if len(parts) >= 4:
            commits.append({
                'hash': parts[0],
                'message': parts[1],
                'author': parts[2],
                'date': parts[3],
            })
    
    return commits


def get_remote_url(path: Optional[str] = None) -> Optional[str]:
    """Get the remote URL.
    
    Args:
        path: Path within the repository
        
    Returns:
        Remote URL, or None if not available
    """
    _, stdout, _ = run_git_command(["remote", "get-url", "origin"], cwd=path)
    return stdout if stdout else None

"""
Claude Code Python - Worktree Tools
Git worktree management for isolated agent sessions.
"""

from __future__ import annotations

import os
import subprocess
from typing import Any, Optional
from uuid import uuid4

from claude_code.tools.base import Tool, ToolContext, ToolResult, ToolCallback


class EnterWorktreeTool(Tool):
    """Create a git worktree and switch to it.
    
    This tool creates a new git worktree for isolated development,
    allowing parallel feature development without affecting the
    main repository.
    
    Attributes:
        name: enter_worktree
        description: Create a git worktree for isolated work
    """
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "enter_worktree"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "Create a git worktree for isolated work"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input.
        
        Returns:
            JSON schema defining the input parameters.
        """
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name for the worktree"
                },
                "branch": {
                    "type": "string",
                    "description": "Branch name (default: auto-generated)"
                },
                "path": {
                    "type": "string",
                    "description": "Custom path for worktree"
                }
            },
            "required": ["name"]
        }
    
    def is_read_only(self) -> bool:
        """Tool modifies system state by creating worktrees.
        
        Returns:
            False since this tool creates git worktrees.
        """
        return False
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the worktree creation.
        
        Args:
            input_data: Dictionary with 'name', optional 'branch' and 'path'.
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with worktree creation status.
        """
        name = input_data.get("name", "")
        branch = input_data.get("branch", "")
        custom_path = input_data.get("path", "")
        
        if not name:
            return ToolResult(content="Error: name is required", is_error=True)
        
        cwd = context.working_directory
        
        if not branch:
            branch = f"claude-{name}-{str(uuid4())[:8]}"
        
        worktree_base = ".claude-worktrees"
        worktree_path = custom_path or os.path.join(cwd, worktree_base, name)
        
        try:
            os.makedirs(os.path.dirname(worktree_path), exist_ok=True)
            
            result = subprocess.run(
                ["git", "worktree", "add", worktree_path, "-b", branch],
                cwd=cwd,
                capture_output=True,
                text=True,
            )
            
            if result.returncode != 0:
                return ToolResult(
                    content=f"Failed to create worktree: {result.stderr}",
                    is_error=True
                )
            
            return ToolResult(content=f"""# Worktree Created

**Name:** {name}
**Branch:** {branch}
**Path:** {worktree_path}

Working directory has been switched to the worktree.

Use /exit_worktree to return and clean up.""")
            
        except FileNotFoundError:
            return ToolResult(content="Git not found", is_error=True)
        except Exception as e:
            return ToolResult(content=f"Error: {str(e)}", is_error=True)


class ExitWorktreeTool(Tool):
    """Exit worktree and return to main repository.
    
    This tool exits the current git worktree and optionally
    cleans up the worktree directory.
    
    Attributes:
        name: exit_worktree
        description: Exit worktree and return to main directory
    """
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "exit_worktree"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "Exit worktree and return to main directory"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input.
        
        Returns:
            JSON schema defining the input parameters.
        """
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of worktree to exit"
                },
                "cleanup": {
                    "type": "boolean",
                    "description": "Remove worktree after exiting",
                    "default": False
                }
            },
            "required": []
        }
    
    def is_read_only(self) -> bool:
        """Tool modifies system state by exiting worktrees.
        
        Returns:
            False since this tool can remove worktrees.
        """
        return False
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the worktree exit.
        
        Args:
            input_data: Dictionary with optional 'name' and 'cleanup'.
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with exit status.
        """
        name = input_data.get("name", "")
        cleanup = input_data.get("cleanup", True)
        
        cwd = context.working_directory
        worktree_base = ".claude-worktrees"
        
        if not name:
            if worktree_base in cwd and cwd.endswith(name):
                name = os.path.basename(cwd)
            else:
                return ToolResult(
                    content="Error: name is required or run from within worktree",
                    is_error=True
                )
        
        worktree_path = os.path.join(cwd.replace(os.path.basename(cwd), "").rstrip("/"), worktree_base, name)
        
        if not os.path.exists(worktree_path):
            return ToolResult(content=f"Worktree not found: {name}", is_error=True)
        
        try:
            main_repo = os.path.dirname(os.path.dirname(worktree_path))
            
            if cleanup:
                subprocess.run(
                    ["git", "worktree", "remove", "--force", worktree_path],
                    capture_output=True,
                )
                
                branch = f"claude-{name}"
                subprocess.run(
                    ["git", "branch", "-d", branch],
                    cwd=main_repo,
                    capture_output=True,
                )
            
            return ToolResult(content=f"""# Worktree Exited

Worktree: {name}
Cleaned up: {cleanup}

Returned to: {main_repo}""")
            
        except Exception as e:
            return ToolResult(content=f"Error: {str(e)}", is_error=True)


class ListWorktreesTool(Tool):
    """List all git worktrees.
    
    This tool lists all git worktrees in the current repository,
    including the main working directory.
    
    Attributes:
        name: list_worktrees
        description: List all git worktrees
    """
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "list_worktrees"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "List all git worktrees"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input.
        
        Returns:
            JSON schema (no parameters required).
        """
        return {"type": "object", "properties": {}}
    
    def is_read_only(self) -> bool:
        """Tool only reads worktree information.
        
        Returns:
            True since listing is a read operation.
        """
        return True
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the worktree listing.
        
        Args:
            input_data: Empty dictionary (no parameters).
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with list of worktrees.
        """
        try:
            result = subprocess.run(
                ["git", "worktree", "list"],
                cwd=context.working_directory,
                capture_output=True,
                text=True,
            )
            
            if result.returncode != 0:
                return ToolResult(content="Not a git repository", is_error=True)
            
            lines: list[str] = ["# Git Worktrees\n"]
            
            for line in result.stdout.strip().split("\n"):
                lines.append(line)
            
            return ToolResult(content="\n".join(lines))
            
        except Exception as e:
            return ToolResult(content=f"Error: {str(e)}", is_error=True)


__all__ = ["EnterWorktreeTool", "ExitWorktreeTool", "ListWorktreesTool"]

"""
Claude Code Python - Team Tools
Team management for multi-agent collaboration.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- pathlib.Path for file operations
"""

from __future__ import annotations

import os
import json
from typing import Any, Optional
from pathlib import Path
from uuid import uuid4
from datetime import datetime

from claude_code.tools.base import Tool, ToolContext, ToolResult, ToolCallback


class TeamCreateTool(Tool):
    """Create a team of agents for multi-agent collaboration.
    
    This tool creates a team configuration that can be used to
    coordinate multiple Claude Code agents working together on
    a shared task.
    
    Attributes:
        name: team_create
        description: Create a team for multi-agent collaboration
    """
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "team_create"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "Create a team for multi-agent collaboration"
    
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
                    "description": "Name for the team"
                },
                "description": {
                    "type": "string",
                    "description": "Description of the team's purpose"
                },
                "members": {
                    "type": "array",
                    "description": "Initial team members (agent identifiers)",
                    "items": {"type": "string"}
                }
            },
            "required": ["name"]
        }
    
    def is_read_only(self) -> bool:
        """Tool modifies system state by creating teams.
        
        Returns:
            False since this tool creates team configurations.
        """
        return False
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the team creation.
        
        Args:
            input_data: Dictionary with 'name', optional 'description', 'members'.
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with team creation status.
        """
        name = input_data.get("name", "")
        description = input_data.get("description", "")
        members = input_data.get("members", [])
        
        if not name:
            return ToolResult(content="Error: name is required", is_error=True)
        
        team_file = Path(context.working_directory) / ".claude" / "teams.json"
        team_file.parent.mkdir(exist_ok=True)
        
        teams = {}
        if team_file.exists():
            with open(team_file) as f:
                teams = json.load(f)
        
        if name in teams:
            return ToolResult(content=f"Team already exists: {name}", is_error=True)
        
        teams[name] = {
            "id": str(uuid4()),
            "name": name,
            "description": description,
            "members": members,
            "created_at": None,
        }
        
        with open(team_file, "w") as f:
            json.dump(teams, f, indent=2)
        
        return ToolResult(content=f"""# Team Created

**Name:** {name}
**Description:** {description}
**Members:** {', '.join(members) if members else 'None'}

Use /team add to add members.""")


class TeamDeleteTool(Tool):
    """Delete a team.
    
    This tool removes a team configuration from the system.
    
    Attributes:
        name: team_delete
        description: Delete a team
    """
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "team_delete"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "Delete a team"
    
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
                    "description": "Name of the team to delete"
                }
            },
            "required": ["name"]
        }
    
    def is_read_only(self) -> bool:
        """Tool modifies system state by deleting teams.
        
        Returns:
            False since this tool removes team configurations.
        """
        return False
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the team deletion.
        
        Args:
            input_data: Dictionary with 'name'.
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with deletion status.
        """
        name = input_data.get("name", "")
        
        if not name:
            return ToolResult(content="Error: name is required", is_error=True)
        
        team_file = Path(context.working_directory) / ".claude" / "teams.json"
        
        if not team_file.exists():
            return ToolResult(content=f"Team not found: {name}", is_error=True)
        
        with open(team_file) as f:
            teams = json.load(f)
        
        if name not in teams:
            return ToolResult(content=f"Team not found: {name}", is_error=True)
        
        del teams[name]
        
        with open(team_file, "w") as f:
            json.dump(teams, f, indent=2)
        
        return ToolResult(content=f"Deleted team: {name}")


class TeamAddMemberTool(Tool):
    """Add a member to a team.
    
    This tool adds an agent member to an existing team.
    
    Attributes:
        name: team_add_member
        description: Add a member to a team
    """
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "team_add_member"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "Add a member to a team"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input.
        
        Returns:
            JSON schema defining the input parameters.
        """
        return {
            "type": "object",
            "properties": {
                "team": {
                    "type": "string",
                    "description": "Name of the team to add member to"
                },
                "member": {
                    "type": "string",
                    "description": "Agent identifier to add as member"
                }
            },
            "required": ["team", "member"]
        }
    
    def is_read_only(self) -> bool:
        """Tool modifies system state by adding team members.
        
        Returns:
            False since this tool modifies team configuration.
        """
        return False
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the member addition.
        
        Args:
            input_data: Dictionary with 'team' and 'member'.
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with addition status.
        """
        team_name = input_data.get("team", "")
        member = input_data.get("member", "")
        
        team_file = Path(context.working_directory) / ".claude" / "teams.json"
        
        if not team_file.exists():
            return ToolResult(content=f"Team not found: {team_name}", is_error=True)
        
        with open(team_file) as f:
            teams = json.load(f)
        
        if team_name not in teams:
            return ToolResult(content=f"Team not found: {team_name}", is_error=True)
        
        if member not in teams[team_name]["members"]:
            teams[team_name]["members"].append(member)
        
        with open(team_file, "w") as f:
            json.dump(teams, f, indent=2)
        
        return ToolResult(content=f"Added {member} to team {team_name}")


class TeamListTool(Tool):
    """List all teams.
    
    This tool displays all configured teams and their members.
    
    Attributes:
        name: team_list
        description: List all teams
    """
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "team_list"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "List all teams"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input.
        
        Returns:
            JSON schema (no parameters required).
        """
        return {"type": "object", "properties": {}}
    
    def is_read_only(self) -> bool:
        """Tool only reads team information.
        
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
        """Execute the team listing.
        
        Args:
            input_data: Empty dictionary (no parameters).
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with list of teams.
        """
        team_file = Path(context.working_directory) / ".claude" / "teams.json"
    
    def is_read_only(self) -> bool:
        return True
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the team listing.
        
        Args:
            input_data: Empty dictionary (no parameters).
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with list of teams.
        """
        team_file = Path(context.working_directory) / ".claude" / "teams.json"
        
        if not team_file.exists():
            return ToolResult(content="No teams configured")
        
        with open(team_file) as f:
            teams = json.load(f)
        
        if not teams:
            return ToolResult(content="No teams configured")
        
        lines = ["# Teams\n"]
        
        for name, info in teams.items():
            lines.append(f"\n## {name}")
            lines.append(f"Description: {info.get('description', 'N/A')}")
            lines.append(f"Members: {', '.join(info.get('members', []))}")
        
        return ToolResult(content="\n".join(lines))


__all__ = ["TeamCreateTool", "TeamDeleteTool", "TeamAddMemberTool", "TeamListTool"]

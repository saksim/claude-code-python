"""
Claude Code Python - Terminal Capture Tool
Terminal session capture and recording.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- pathlib.Path for file operations
"""

from __future__ import annotations

import os
import json
import subprocess
from typing import Any, Optional
from pathlib import Path
from datetime import datetime

from claude_code.tools.base import Tool, ToolContext, ToolResult, ToolCallback


class TerminalCaptureTool(Tool):
    """Capture terminal session output for recording and replay.
    
    This tool provides terminal session capture functionality,
    allowing users to record terminal sessions and replay them later.
    
    Supported actions:
        - start: Begin capturing terminal output
        - stop: Stop capturing terminal output
        - save: Save captured session to file
        - replay: Replay a saved session
    
    Attributes:
        name: terminal_capture
        description: Capture terminal session for recording/replay
    """
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "terminal_capture"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "Capture terminal session for recording/replay"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input.
        
        Returns:
            JSON schema defining the input parameters.
        """
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["start", "stop", "save", "replay"],
                    "description": "Action to perform (start, stop, save, replay)"
                },
                "session_name": {
                    "type": "string",
                    "description": "Name for the capture session"
                },
                "output_file": {
                    "type": "string",
                    "description": "Path to save the capture file"
                }
            },
            "required": ["action"]
        }
    
    def is_read_only(self) -> bool:
        """Tool modifies system state by capturing terminal.
        
        Returns:
            False since this tool records terminal output.
        """
        return False
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the terminal capture action.
        
        Args:
            input_data: Dictionary with 'action' and action-specific parameters.
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with action result.
        """
        action = input_data.get("action", "")
        session_name = input_data.get("session_name", "default")
        output_file = input_data.get("output_file", "")
        
        captures_dir = Path(context.working_directory) / ".claude" / "captures"
        captures_dir.mkdir(exist_ok=True)
        
        if action == "start":
            capture_file = captures_dir / f"{session_name}.json"
            
            capture_data = {
                "session": session_name,
                "started_at": datetime.now().isoformat(),
                "commands": [],
                "output": [],
            }
            
            with open(capture_file, "w") as f:
                json.dump(capture_data, f)
            
            return ToolResult(content=f"Started capture: {session_name}")
        
        elif action == "stop":
            capture_file = captures_dir / f"{session_name}.json"
            
            if not capture_file.exists():
                return ToolResult(content="No active capture", is_error=True)
            
            with open(capture_file) as f:
                capture_data = json.load(f)
            
            capture_data["ended_at"] = datetime.now().isoformat()
            
            with open(capture_file, "w") as f:
                json.dump(capture_data, f)
            
            return ToolResult(content=f"Stopped capture: {session_name}")
        
        elif action == "save":
            capture_file = captures_dir / f"{session_name}.json"
            save_file = output_file or captures_dir / f"{session_name}_saved.json"
            
            if not capture_file.exists():
                return ToolResult(content="Capture not found", is_error=True)
            
            capture_file.rename(save_file)
            
            return ToolResult(content=f"Saved capture to: {save_file}")
        
        elif action == "replay":
            capture_file = captures_dir / f"{session_name}.json"
            
            if not capture_file.exists():
                return ToolResult(content="Capture not found", is_error=True)
            
            with open(capture_file) as f:
                capture_data = json.load(f)
            
            lines = [f"# Terminal Capture: {session_name}\n"]
            lines.append(f"Commands: {len(capture_data.get('commands', []))}")
            
            return ToolResult(content="\n".join(lines))
        
        return ToolResult(content=f"Unknown action: {action}", is_error=True)


__all__ = ["TerminalCaptureTool"]

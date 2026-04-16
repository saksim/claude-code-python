"""
Claude Code Python - Cron Create Tool
Schedule recurring or one-shot prompt tasks.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Dataclass patterns
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from claude_code.tools.base import Tool, ToolContext, ToolResult, ToolCallback


DEFAULT_MAX_AGE_DAYS = 14
MAX_JOBS = 50
_SESSION_ONLY_TASKS: dict[str, dict[str, Any]] = {}


@dataclass(frozen=True, slots=True)
class CronValidationResult:
    """Result of cron expression validation."""
    valid: bool
    message: str
    error_code: int


def parse_cron_expression(cron: str) -> bool:
    """Validate a 5-field cron expression.
    
    Args:
        cron: Cron expression string (M H DoM Mon DoW)
        
    Returns:
        True if valid, False otherwise
    """
    pattern = r'^(\d+|\*)(\/(\d+))?\s+(\d+|\*)(\/(\d+))?\s+(\d+|\*)(\/(\d+))?\s+(\d+|\*)(\/(\d+))?\s+(\d+|\*)(\/(\d+))?$'
    return bool(re.match(pattern, cron))


def cron_to_human(cron: str) -> str:
    """Convert cron expression to human-readable format.
    
    Args:
        cron: Cron expression string
        
    Returns:
        Human-readable schedule description
    """
    parts = cron.split()
    if len(parts) != 5:
        return cron
    
    minute, hour, dom, mon, dow = parts
    
    descriptions = []
    
    if minute == '*':
        descriptions.append("every minute")
    elif minute.startswith('*/'):
        descriptions.append(f"every {minute[2:]} minutes")
    else:
        descriptions.append(f"at minute {minute}")
    
    if hour != '*':
        if hour.startswith('*/'):
            descriptions.append(f"every {hour[2:]} hours")
        else:
            descriptions.append(f"at {hour}:00")
    
    if dom != '*':
        descriptions.append(f"on day {dom}")
    
    if mon != '*':
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        if mon.isdigit() and 1 <= int(mon) <= 12:
            descriptions.append(f"in {month_names[int(mon)-1]}")
        else:
            descriptions.append(f"in month {mon}")
    
    if dow != '*':
        days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        if dow.isdigit() and 0 <= int(dow) <= 6:
            descriptions.append(f"on {days[int(dow)]}")
        else:
            descriptions.append(f"on day {dow}")
    
    return ", ".join(descriptions) if descriptions else cron


def _load_persisted_tasks(schedule_file: Path) -> dict[str, dict[str, Any]]:
    """Load persisted cron tasks from disk."""
    if not schedule_file.exists():
        return {}
    try:
        with open(schedule_file, encoding="utf-8") as f:
            payload = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _save_persisted_tasks(schedule_file: Path, tasks: dict[str, dict[str, Any]]) -> None:
    """Persist cron tasks atomically."""
    schedule_file.parent.mkdir(parents=True, exist_ok=True)
    temp_file = schedule_file.with_name(f"{schedule_file.name}.{uuid4().hex}.tmp")
    payload = json.dumps(tasks, indent=2)
    temp_file.write_text(payload, encoding="utf-8")
    try:
        temp_file.replace(schedule_file)
    except PermissionError:
        schedule_file.write_text(payload, encoding="utf-8")


class CronCreateTool(Tool):
    """Create a scheduled cron job.
    
    This tool schedules a prompt to run at specified intervals using
    cron syntax. Supports both recurring and one-shot tasks.
    
    Attributes:
        name: cron_create
        description: Create a scheduled task
    """
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "cron_create"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "Schedule a recurring or one-shot prompt"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input.
        
        Returns:
            JSON schema defining the input parameters.
        """
        return {
            "type": "object",
            "properties": {
                "cron": {
                    "type": "string",
                    "description": 'Standard 5-field cron expression in local time: "M H DoM Mon DoW" (e.g. "*/5 * * * *" = every 5 minutes, "30 14 28 2 *" = Feb 28 at 2:30pm local once).'
                },
                "prompt": {
                    "type": "string",
                    "description": "The prompt to enqueue at each fire time."
                },
                "recurring": {
                    "type": "boolean",
                    "description": f"true (default) = fire on every cron match until deleted or auto-expired after {DEFAULT_MAX_AGE_DAYS} days. false = fire once at the next match, then auto-delete.",
                    "default": True
                },
                "durable": {
                    "type": "boolean",
                    "description": "true = persist to .claude/scheduled_tasks.json and survive restarts. false (default) = in-memory only, dies when this Claude session ends.",
                    "default": False
                }
            },
            "required": ["cron", "prompt"]
        }
    
    def is_read_only(self) -> bool:
        """Tool modifies system state by creating schedules.
        
        Returns:
            False since this tool creates scheduled tasks.
        """
        return False
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the cron job creation.
        
        Args:
            input_data: Dictionary with 'cron', 'prompt', optional 'recurring', 'durable'.
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with schedule creation status.
        """
        cron = input_data.get("cron", "")
        prompt = input_data.get("prompt", "")
        recurring = input_data.get("recurring", True)
        durable = input_data.get("durable", False)
        
        validation = self._validate_input(cron, prompt, recurring, durable, context)
        if not validation.valid:
            return ToolResult(content=validation.message, is_error=True)
        
        task_id = str(uuid4())[:12]
        human_schedule = cron_to_human(cron)
        
        schedule_file = Path(context.working_directory) / ".claude" / "scheduled_tasks.json"
        task_payload: dict[str, Any] = {
            "cron": cron,
            "prompt": prompt,
            "recurring": recurring,
            "durable": durable,
            "created_at": datetime.now().isoformat(),
            "last_run": None,
            "status": "active"
        }

        if durable:
            tasks = _load_persisted_tasks(schedule_file)
            tasks[task_id] = task_payload
            _save_persisted_tasks(schedule_file, tasks)
        else:
            _SESSION_ONLY_TASKS[task_id] = task_payload
        
        location = "Persisted to .claude/scheduled_tasks.json" if durable else "Session-only (not written to disk)"
        
        if recurring:
            message = f"Scheduled recurring job {task_id} ({human_schedule}). {location}. Auto-expires after {DEFAULT_MAX_AGE_DAYS} days. Use CronDelete to cancel sooner."
        else:
            message = f"Scheduled one-shot task {task_id} ({human_schedule}). {location}. It will fire once then auto-delete."
        
        return ToolResult(content=message)
    
    def _validate_input(
        self,
        cron: str,
        prompt: str,
        recurring: bool,
        durable: bool,
        context: ToolContext
    ) -> CronValidationResult:
        """Validate cron job input.
        
        Args:
            cron: Cron expression
            prompt: Prompt text
            recurring: Whether task is recurring
            durable: Whether task persists
            context: Tool execution context
            
        Returns:
            CronValidationResult with validation status
        """
        if not parse_cron_expression(cron):
            return CronValidationResult(
                valid=False,
                message=f"Invalid cron expression '{cron}'. Expected 5 fields: M H DoM Mon DoW.",
                error_code=1
            )
        
        schedule_file = Path(context.working_directory) / ".claude" / "scheduled_tasks.json"
        
        task_count = 0
        if durable:
            task_count = len(_load_persisted_tasks(schedule_file))
        else:
            task_count = len(_SESSION_ONLY_TASKS)
        
        if task_count >= MAX_JOBS:
            return CronValidationResult(
                valid=False,
                message=f"Too many scheduled jobs (max {MAX_JOBS}). Cancel one first.",
                error_code=3
            )
        
        return CronValidationResult(valid=True, message="", error_code=0)


__all__ = ["CronCreateTool", "CronValidationResult", "cron_to_human", "parse_cron_expression"]

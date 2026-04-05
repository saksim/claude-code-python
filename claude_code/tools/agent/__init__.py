"""
Claude Code Python - Agent Tool
Spawn and manage sub-agents for task execution.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Dataclass patterns
"""

from __future__ import annotations

import asyncio
import os
from typing import Any, Optional
from uuid import uuid4
from dataclasses import dataclass, field

from claude_code.tools.base import Tool, ToolContext, ToolResult, ToolCallback


@dataclass(frozen=True, slots=True)
class AgentDefinition:
    """Definition of an agent type.
    
    Using frozen=True, slots=True for immutability.
    
    Attributes:
        agent_type: Type identifier for the agent
        description: Human-readable description
        prompt: System prompt for the agent
        model: Model to use (default: sonnet)
        background: Whether agent runs in background
        isolation: Isolation mode for the agent
        permission_mode: Permission mode for the agent
    """
    agent_type: str
    description: str
    prompt: str
    model: str = "sonnet"
    background: bool = False
    isolation: Optional[str] = None
    permission_mode: str = "acceptEdits"


BUILTIN_AGENTS: dict[str, AgentDefinition] = {
    "general-purpose": AgentDefinition(
        agent_type="general-purpose",
        description="General purpose agent for any task",
        prompt="You are a helpful AI assistant.",
    ),
    "editor": AgentDefinition(
        agent_type="editor",
        description="Agent specialized in file editing",
        prompt="You are a code editing agent. Make precise edits to files.",
    ),
    "reviewer": AgentDefinition(
        agent_type="reviewer",
        description="Agent specialized in code review",
        prompt="You are a code review agent. Analyze code for issues.",
    ),
    "researcher": AgentDefinition(
        agent_type="researcher",
        description="Agent specialized in research and information gathering",
        prompt="You are a research agent. Gather and summarize information.",
    ),
}


class AgentTool(Tool):
    """Tool to spawn sub-agents for task execution.
    
    This tool allows the AI to spawn independent sub-agents that
    can work on tasks in parallel or background. Sub-agents can
    be configured with different agent types and permission modes.
    
    Attributes:
        name: agent
        description: Spawn a sub-agent to perform a task
    """
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "agent"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "Spawn a sub-agent to perform a task. The agent runs independently and reports results."
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input.
        
        Returns:
            JSON schema defining the input parameters.
        """
        return {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "A short (3-5 word) description of the task"
                },
                "prompt": {
                    "type": "string",
                    "description": "The task for the agent to perform"
                },
                "subagent_type": {
                    "type": "string",
                    "description": "The type of specialized agent to use",
                    "enum": list(BUILTIN_AGENTS.keys()),
                },
                "model": {
                    "type": "string",
                    "description": "Optional model override (sonnet, opus, haiku)",
                    "enum": ["sonnet", "opus", "haiku"],
                },
                "run_in_background": {
                    "type": "boolean",
                    "description": "Run this agent in the background"
                },
                "name": {
                    "type": "string",
                    "description": "Name for the spawned agent"
                },
                "isolation": {
                    "type": "string",
                    "description": "Isolation mode (worktree)",
                    "enum": ["worktree"],
                },
                "cwd": {
                    "type": "string",
                    "description": "Working directory for the agent"
                },
            },
            "required": ["description", "prompt"]
        }
    
    def is_read_only(self) -> bool:
        return False
    
    def is_concurrency_safe(self) -> bool:
        return True
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the sub-agent spawn.
        
        Args:
            input_data: Dictionary with agent configuration parameters.
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with agent execution status.
        """
        description = input_data.get("description", "")
        prompt = input_data.get("prompt", "")
        subagent_type = input_data.get("subagent_type", "general-purpose")
        model = input_data.get("model")
        run_in_background = input_data.get("run_in_background", False)
        name = input_data.get("name")
        isolation = input_data.get("isolation")
        cwd = input_data.get("cwd")
        
        if not description:
            return ToolResult(
                content="Error: description is required",
                is_error=True
            )
        
        if not prompt:
            return ToolResult(
                content="Error: prompt is required",
                is_error=True
            )
        
        agent_id = str(uuid4())[:8]
        agent_name = name or f"agent-{agent_id}"
        
        agent_def = BUILTIN_AGENTS.get(subagent_type)
        if not agent_def:
            return ToolResult(
                content=f"Unknown agent type: {subagent_type}. Available: {', '.join(BUILTIN_AGENTS.keys())}",
                is_error=True
            )
        
        effective_cwd = cwd or context.working_directory
        
        effective_model = model or agent_def.model
        
        if run_in_background:
            return await self._run_async_agent(
                agent_name=agent_name,
                description=description,
                prompt=prompt,
                agent_def=agent_def,
                model=effective_model,
                isolation=isolation,
                cwd=effective_cwd,
                context=context,
                on_progress=on_progress,
            )
        else:
            return await self._run_sync_agent(
                agent_name=agent_name,
                description=description,
                prompt=prompt,
                agent_def=agent_def,
                model=effective_model,
                isolation=isolation,
                cwd=effective_cwd,
                context=context,
                on_progress=on_progress,
            )
    
    async def _run_sync_agent(
        self,
        agent_name: str,
        description: str,
        prompt: str,
        agent_def: AgentDefinition,
        model: str,
        isolation: Optional[str],
        cwd: str,
        context: ToolContext,
        on_progress: Optional[ToolCallback],
    ) -> ToolResult:
        """Run agent synchronously."""
        from .claude_code.engine.query import QueryEngine
        from .claude_code.api.client import APIClient, APIClientConfig
        
        worktree_path = None
        if isolation == "worktree":
            worktree_path = await self._create_worktree(agent_name, cwd)
            if worktree_path:
                cwd = worktree_path
        
        try:
            api_config = APIClientConfig()
            api_client = APIClient(api_config)
            
            system_prompt = f"""{agent_def.prompt}

You are executing as a sub-agent of Claude Code. Your task is:
{prompt}

Working directory: {cwd}

Report your findings and results clearly."""
            
            engine = QueryEngine(
                api_client=api_client,
                config=None,
                tool_registry=None,
            )
            
            engine.config.system_prompt = system_prompt
            if model:
                engine.config.model = f"claude-{model}-4-20250514"
            
            result_parts = []
            async for event in engine.query(prompt):
                from .claude_code.engine.query import Message, ToolUse, ToolCallResult
                if isinstance(event, Message) and event.role == "assistant":
                    if isinstance(event.content, str):
                        result_parts.append(event.content)
                elif isinstance(event, dict):
                    if event.get("type") == "text":
                        result_parts.append(event.get("content", ""))
            
            result = "\n".join(result_parts) if result_parts else "Agent completed with no output"
            
            return ToolResult(content=f"[{agent_name}] {description}\n\n{result}")
            
        except Exception as e:
            return ToolResult(
                content=f"Agent error: {str(e)}",
                is_error=True
            )
        finally:
            if worktree_path:
                await self._cleanup_worktree(worktree_path)
    
    async def _run_async_agent(
        self,
        agent_name: str,
        description: str,
        prompt: str,
        agent_def: AgentDefinition,
        model: str,
        isolation: Optional[str],
        cwd: str,
        context: ToolContext,
        on_progress: Optional[ToolCallback],
    ) -> ToolResult:
        """Run agent asynchronously in background."""
        from ...tasks.manager import TaskManager
        from ...tasks.types import TaskType, BashTask
        
        task_manager = TaskManager()
        
        task = await task_manager.create_agent_task(
            prompt=prompt,
            model=model,
            background=True,
            description=description,
            cwd=cwd,
        )
        
        return ToolResult(
            content=f"""Started background agent: {agent_name}
Task ID: {task.id}
Description: {description}

Use /tasks to monitor progress."""
        )
    
    async def _create_worktree(self, name: str, cwd: str) -> Optional[str]:
        """Create a git worktree for isolation."""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "worktree", "add", f".claude-worktrees/{name}", "-b", f"claude-{name}"],
                cwd=cwd,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return os.path.join(cwd, ".claude-worktrees", name)
            return None
        except Exception:
            return None
    
    async def _cleanup_worktree(self, worktree_path: str) -> None:
        """Cleanup worktree after agent completes."""
        try:
            import subprocess
            worktree_dir = os.path.dirname(worktree_path)
            branch_name = os.path.basename(worktree_path)
            subprocess.run(
                ["git", "worktree", "remove", "--force", worktree_path],
                capture_output=True,
            )
            subprocess.run(
                ["git", "branch", "-d", f"claude-{branch_name}"],
                cwd=os.path.dirname(worktree_path),
                capture_output=True,
            )
        except Exception:
            pass


__all__ = ["AgentTool", "AgentDefinition", "BUILTIN_AGENTS"]

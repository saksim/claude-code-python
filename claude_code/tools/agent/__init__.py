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
import json
from typing import Any, Optional
from uuid import uuid4
from dataclasses import dataclass, field

from claude_code.tools.base import Tool, ToolContext, ToolResult, ToolCallback
from claude_code.agents.builtin import (
    AgentDefinition,
    create_builtin_agents,
    setup_builtin_agents,
)
from claude_code.agents.loader import load_agents_from_directory
from claude_code.services.multi_agent_supervisor import (
    AgentNodeSpec,
    MultiAgentSupervisor,
    SupervisorBudget,
    SupervisorConfigError,
)

_MODEL_ALIASES: dict[str, str] = {
    "haiku": "claude-haiku-20240307",
    "sonnet": "claude-sonnet-4-20250514",
    "opus": "claude-opus-4-20250514",
    "sonnet-4": "claude-sonnet-4-20250514",
    "opus-4": "claude-opus-4-20250514",
}


def _resolve_model_name(model: str) -> str:
    """Resolve a short model alias to a full runtime model id."""
    if not model:
        return _MODEL_ALIASES["sonnet"]
    if model in _MODEL_ALIASES:
        return _MODEL_ALIASES[model]
    if model.startswith("claude-"):
        return model
    return model


def _resolve_runtime_provider(model_provider: Optional[str]) -> str:
    """Normalize runtime provider string for sub-agent API-client config."""
    candidate = (model_provider or "").strip().lower()
    if candidate in {"anthropic", "openai", "ollama", "vllm", "deepseek", "bedrock", "vertex"}:
        return candidate
    return "anthropic"


def _resolve_runtime_model(*, model: str, fallback_model: Optional[str]) -> str:
    """Resolve sub-agent model with fallback to parent runtime model when needed."""
    resolved = _resolve_model_name(model)
    if resolved.startswith("claude-") and fallback_model and not str(fallback_model).startswith("claude-"):
        return str(fallback_model)
    return resolved


def _build_subagent_system_prompt(
    agent_prompt: str,
    task_prompt: str,
    working_directory: str,
) -> str:
    """Build consistent system prompt for sync/background sub-agents."""
    return f"""{agent_prompt}

You are executing as a sub-agent of Claude Code. Your task is:
{task_prompt}

Working directory: {working_directory}

Report your findings and results clearly."""


def _build_agent_registry() -> dict[str, AgentDefinition]:
    """Build the complete agent registry from builtin agents.
    
    Returns:
        Dictionary mapping agent_type to AgentDefinition.
    """
    return create_builtin_agents()


# Complete agent registry, built from the unified agents/builtin.py
BUILTIN_AGENTS: dict[str, AgentDefinition] = _build_agent_registry()

# Ensure legacy AGENTS dict is also populated
setup_builtin_agents()


class AgentTool(Tool):
    """Tool to spawn sub-agents for task execution.
    
    This tool allows the AI to spawn independent sub-agents that
    can work on tasks in parallel or background. Sub-agents can
    be configured with different agent types and permission modes.
    
    Attributes:
        name: agent
        description: Spawn a sub-agent to perform a task
    """

    def __init__(self) -> None:
        super().__init__()
        self._custom_agents: dict[str, AgentDefinition] = {}
        self._custom_agents_loaded_from: Optional[str] = None
    
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
                    "description": (
                        "The type of specialized agent to use. "
                        "Supports built-in and .claude/agents custom agent names."
                    ),
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
                "orchestrate": {
                    "type": "boolean",
                    "description": "Run a multi-agent DAG workflow instead of a single sub-agent",
                },
                "workflow": {
                    "type": "object",
                    "description": "Workflow DAG payload when orchestrate=true",
                    "properties": {
                        "id": {"type": "string"},
                        "nodes": {
                            "type": "array",
                            "items": {"type": "object"},
                        },
                        "budget": {"type": "object"},
                        "timeout_seconds": {"type": "number"},
                    },
                    "required": ["nodes"],
                },
            },
            "required": ["description", "prompt"]
        }
    
    def is_read_only(self) -> bool:
        return False
    
    def is_concurrency_safe(self) -> bool:
        return True

    def _ensure_custom_agents_loaded(self, cwd: str) -> None:
        """Lazy-load custom agents for current workspace."""
        normalized = os.path.abspath(cwd)
        if self._custom_agents_loaded_from == normalized:
            return
        self._custom_agents = load_agents_from_directory(normalized)
        self._custom_agents_loaded_from = normalized
    
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
        orchestrate = bool(input_data.get("orchestrate", False))
        workflow = input_data.get("workflow")
        
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

        self._ensure_custom_agents_loaded(context.working_directory)

        agent_id = str(uuid4())[:8]
        agent_name = name or f"agent-{agent_id}"

        agent_def = self._custom_agents.get(subagent_type) or BUILTIN_AGENTS.get(subagent_type)
        if not agent_def:
            available = sorted(set(self._custom_agents.keys()) | set(BUILTIN_AGENTS.keys()))
            return ToolResult(
                content=f"Unknown agent type: {subagent_type}. Available: {', '.join(available)}",
                is_error=True
            )
        
        effective_cwd = cwd or context.working_directory

        if orchestrate:
            return await self._run_supervisor_workflow(
                description=description,
                prompt=prompt,
                workflow=workflow,
                cwd=effective_cwd,
                context=context,
            )
        
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

    async def _run_supervisor_workflow(
        self,
        *,
        description: str,
        prompt: str,
        workflow: Any,
        cwd: str,
        context: ToolContext,
    ) -> ToolResult:
        """Run P2-01 DAG supervisor workflow."""
        try:
            workflow_payload = workflow if isinstance(workflow, dict) else {}
            nodes_payload = workflow_payload.get("nodes")
            if nodes_payload is None:
                raise SupervisorConfigError("workflow.nodes is required when orchestrate=true")
            if not isinstance(nodes_payload, list):
                raise SupervisorConfigError("workflow.nodes must be an array")

            workflow_id = str(workflow_payload.get("id") or f"wf-{uuid4().hex[:8]}")
            budget = SupervisorBudget.from_dict(workflow_payload.get("budget"))
            timeout_raw = workflow_payload.get("timeout_seconds")
            workflow_timeout_seconds = None
            if timeout_raw is not None:
                try:
                    workflow_timeout_seconds = float(timeout_raw)
                except Exception as exc:
                    raise SupervisorConfigError("workflow.timeout_seconds must be a number") from exc
                if workflow_timeout_seconds <= 0:
                    raise SupervisorConfigError("workflow.timeout_seconds must be > 0")

            nodes = [
                AgentNodeSpec.from_dict(item, index=index)
                for index, item in enumerate(nodes_payload)
            ]

            async def _node_executor(
                node: AgentNodeSpec,
                resolved_prompt: str,
                dependency_artifacts: dict[str, dict[str, Any]],
            ) -> str:
                agent_def = BUILTIN_AGENTS.get(node.subagent_type)
                if agent_def is None:
                    raise ValueError(
                        f"Unknown subagent_type '{node.subagent_type}' for node '{node.node_id}'"
                    )
                resolved_model = node.model or agent_def.model
                result = await self._run_sync_agent(
                    agent_name=f"{workflow_id}-{node.node_id}",
                    description=node.description,
                    prompt=resolved_prompt,
                    agent_def=agent_def,
                    model=resolved_model,
                    isolation=agent_def.isolation,
                    cwd=cwd,
                    context=context,
                    on_progress=None,
                )
                if result.is_error:
                    raise RuntimeError(str(result.content))
                return str(result.content)

            supervisor = MultiAgentSupervisor(
                executor=_node_executor,
                budget=budget,
                workflow_timeout_seconds=workflow_timeout_seconds,
            )
            run_result = await supervisor.run(
                workflow_id=workflow_id,
                nodes=nodes,
            )
            summary = self._format_supervisor_summary(
                workflow_id=workflow_id,
                description=description,
                root_prompt=prompt,
                run_result=run_result,
            )
            return ToolResult(content=summary)
        except SupervisorConfigError as exc:
            return ToolResult(content=f"Workflow config error: {exc}", is_error=True)

    def _format_supervisor_summary(
        self,
        *,
        workflow_id: str,
        description: str,
        root_prompt: str,
        run_result: Any,
    ) -> str:
        """Render workflow execution summary."""
        lines = [
            f"[supervisor:{workflow_id}] {description}",
            f"root_prompt: {root_prompt}",
            f"status: {run_result.status}",
            f"duration_ms: {run_result.duration_ms:.2f}",
            "nodes:",
        ]
        for item in run_result.results:
            line = (
                f"- {item.node_id} [{item.status.value}] attempts={item.attempts} "
                f"duration_ms={item.duration_ms:.2f}"
            )
            if item.ownership:
                line += f" ownership={','.join(item.ownership)}"
            if item.error:
                line += f" error={item.error}"
            lines.append(line)
        artifacts = json.dumps(run_result.artifacts_by_node, ensure_ascii=True, indent=2, sort_keys=True)
        lines.append("artifacts:")
        lines.append(artifacts)
        return "\n".join(lines)

    @staticmethod
    def _extract_text_result(event: Any) -> str:
        """Normalize assistant/text stream events to plain text chunks."""
        from claude_code.engine.query import Message

        if isinstance(event, Message) and event.role == "assistant":
            if isinstance(event.content, str):
                return event.content
            if isinstance(event.content, list):
                chunks: list[str] = []
                for block in event.content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        chunks.append(str(block.get("text", "")))
                return "".join(chunks)
        if isinstance(event, dict) and event.get("type") == "text":
            return str(event.get("content", ""))
        return ""
    
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
        from claude_code.engine.query import QueryConfig, QueryEngine
        
        worktree_path = None
        if isolation == "worktree":
            worktree_path = await self._create_worktree(agent_name, cwd)
            if worktree_path:
                cwd = worktree_path
        
        try:
            parent_provider = _resolve_runtime_provider(context.api_provider)
            parent_model = str(context.model) if context.model else None
            system_prompt = _build_subagent_system_prompt(
                agent_prompt=agent_def.prompt,
                task_prompt=prompt,
                working_directory=cwd,
            )
            resolved_model = _resolve_runtime_model(model=model, fallback_model=parent_model)

            from claude_code.main import Config, setup_api_client

            api_client = setup_api_client(
                Config(
                    api_provider=parent_provider,
                    model=resolved_model,
                )
            )

            query_config = QueryConfig(
                model=resolved_model,
                system_prompt=system_prompt,
                permission_mode=context.permission_mode,
                always_allow=list(context.always_allow),
                always_deny=list(context.always_deny),
                working_directory=cwd,
                memory_scope=agent_def.memory or context.memory_scope or "project",
            )
            engine = QueryEngine(
                api_client=api_client,
                config=query_config,
                tool_registry=context.tool_registry,
            )
            if context.task_manager is not None:
                engine.task_manager = context.task_manager

            result_parts = []
            async for event in engine.query(prompt):
                text_chunk = self._extract_text_result(event)
                if text_chunk:
                    result_parts.append(text_chunk)
            
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
        from claude_code.tasks.manager import TaskManager
        from claude_code.engine.query import QueryConfig, QueryEngine
        from claude_code.tasks.types import TaskResult

        task_manager = context.task_manager if isinstance(context.task_manager, TaskManager) else TaskManager.get_instance()
        execution_cwd = cwd
        worktree_path = None
        if isolation == "worktree":
            worktree_path = await self._create_worktree(agent_name, cwd)
            if worktree_path:
                execution_cwd = worktree_path

        parent_provider = _resolve_runtime_provider(context.api_provider)
        parent_model = str(context.model) if context.model else None
        resolved_model = _resolve_runtime_model(model=model, fallback_model=parent_model)
        system_prompt = _build_subagent_system_prompt(
            agent_prompt=agent_def.prompt,
            task_prompt=prompt,
            working_directory=execution_cwd,
        )

        task_metadata = {
            "session_id": context.session_id or "",
            "conversation_id": context.conversation_id or "",
            "working_directory": execution_cwd,
            "permission_mode": context.permission_mode,
            "memory_scope": agent_def.memory or context.memory_scope or "project",
            "provider": parent_provider,
            "model": resolved_model,
            "source_tool": "agent",
        }
        task = await task_manager.create_agent_task(
            prompt=prompt,
            model=resolved_model,
            background=True,
            metadata=task_metadata,
        )
        
        async def _execute_agent(task):
            try:
                from claude_code.main import Config, setup_api_client

                api_client = setup_api_client(
                    Config(
                        api_provider=parent_provider,
                        model=resolved_model,
                    )
                )
                query_config = QueryConfig(
                    model=resolved_model,
                    system_prompt=system_prompt,
                    permission_mode=context.permission_mode,
                    always_allow=list(context.always_allow),
                    always_deny=list(context.always_deny),
                    working_directory=execution_cwd,
                    memory_scope=agent_def.memory or context.memory_scope or "project",
                    session_id=context.session_id,
                )
                engine = QueryEngine(
                    api_client=api_client,
                    config=query_config,
                    tool_registry=context.tool_registry,
                )
                if context.task_manager is not None:
                    engine.task_manager = context.task_manager
                
                result_parts = []
                async for event in engine.query(prompt):
                    text_chunk = self._extract_text_result(event)
                    if text_chunk:
                        result_parts.append(text_chunk)
                
                return TaskResult(
                    code=0,
                    stdout="\n".join(result_parts) if result_parts else "Agent completed with no output",
                )
            finally:
                if worktree_path:
                    await self._cleanup_worktree(worktree_path)
        
        await task_manager.start_task(task.id, executor=_execute_agent)
        
        return ToolResult(
            content=f"Started background agent: {agent_name}\n"
                     f"Task ID: {task.id}\n"
                     f"Description: {description}\n\n"
                     f"Use /tasks to monitor progress."
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

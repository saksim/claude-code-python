"""Runtime tests for P2-01 multi-agent supervisor DAG orchestration."""

from __future__ import annotations

import asyncio
import json
import time

import pytest

from claude_code.services.multi_agent_supervisor import (
    AgentNodeSpec,
    MultiAgentSupervisor,
    NodeExecutionStatus,
    SupervisorBudget,
    SupervisorConfigError,
)
from claude_code.tools.agent import AgentTool
from claude_code.tools.base import ToolContext, ToolResult


@pytest.mark.asyncio
async def test_supervisor_rejects_cyclic_graph():
    async def _executor(node, prompt, deps):
        return "ok"

    supervisor = MultiAgentSupervisor(executor=_executor)
    nodes = [
        AgentNodeSpec(node_id="a", description="a", prompt="a", dependencies=("b",)),
        AgentNodeSpec(node_id="b", description="b", prompt="b", dependencies=("a",)),
    ]

    with pytest.raises(SupervisorConfigError, match="contains a cycle"):
        await supervisor.run(workflow_id="wf-cycle", nodes=nodes)


@pytest.mark.asyncio
async def test_supervisor_budget_and_timeout_state_machine():
    async def _executor(node, prompt, deps):
        if node.node_id == "slow":
            await asyncio.sleep(0.1)
        return f"node:{node.node_id}"

    nodes = [
        AgentNodeSpec(node_id="slow", description="slow", prompt="slow", timeout_seconds=0.01),
        AgentNodeSpec(node_id="next", description="next", prompt="next", dependencies=("slow",)),
    ]
    supervisor = MultiAgentSupervisor(
        executor=_executor,
        budget=SupervisorBudget(max_parallelism=1, max_failures=0),
    )
    result = await supervisor.run(workflow_id="wf-timeout", nodes=nodes)

    by_id = {item.node_id: item for item in result.results}
    assert by_id["slow"].status == NodeExecutionStatus.TIMEOUT
    assert by_id["next"].status == NodeExecutionStatus.SKIPPED
    assert result.success is False


@pytest.mark.asyncio
async def test_supervisor_parallel_scheduling_for_independent_nodes():
    timeline: list[tuple[str, str, float]] = []

    async def _executor(node, prompt, deps):
        timeline.append((node.node_id, "start", time.perf_counter()))
        await asyncio.sleep(0.05)
        timeline.append((node.node_id, "end", time.perf_counter()))
        return f"done:{node.node_id}"

    nodes = [
        AgentNodeSpec(node_id="a", description="a", prompt="a"),
        AgentNodeSpec(node_id="b", description="b", prompt="b"),
    ]
    supervisor = MultiAgentSupervisor(
        executor=_executor,
        budget=SupervisorBudget(max_parallelism=2),
    )
    result = await supervisor.run(workflow_id="wf-parallel", nodes=nodes)
    assert result.success is True

    starts = {node_id: ts for node_id, phase, ts in timeline if phase == "start"}
    assert "a" in starts and "b" in starts
    assert abs(starts["a"] - starts["b"]) < 0.04


@pytest.mark.asyncio
async def test_supervisor_retry_recovery_for_failed_node():
    attempts: dict[str, int] = {}

    async def _executor(node, prompt, deps):
        attempts[node.node_id] = attempts.get(node.node_id, 0) + 1
        if node.node_id == "fragile" and attempts[node.node_id] == 1:
            raise RuntimeError("transient")
        return f"ok:{node.node_id}"

    nodes = [
        AgentNodeSpec(
            node_id="fragile",
            description="fragile",
            prompt="fragile",
            max_retries=1,
        ),
    ]
    supervisor = MultiAgentSupervisor(executor=_executor)
    result = await supervisor.run(workflow_id="wf-retry", nodes=nodes)
    item = result.results[0]
    assert item.status == NodeExecutionStatus.COMPLETED
    assert item.attempts == 2
    assert result.success is True


class _FakeAgentTool(AgentTool):
    async def _run_sync_agent(
        self,
        agent_name: str,
        description: str,
        prompt: str,
        agent_def,
        model: str,
        isolation,
        cwd: str,
        context: ToolContext,
        on_progress,
    ) -> ToolResult:
        return ToolResult(content=f"{agent_name}|{description}|{prompt}")


@pytest.mark.asyncio
async def test_agent_tool_orchestrate_returns_supervisor_summary():
    tool = _FakeAgentTool()
    context = ToolContext(working_directory=".", environment={})

    result = await tool.execute(
        {
            "description": "workflow smoke",
            "prompt": "root task",
            "orchestrate": True,
            "workflow": {
                "id": "wf-agent",
                "nodes": [
                    {"id": "n1", "description": "first", "prompt": "do first"},
                    {
                        "id": "n2",
                        "description": "second",
                        "prompt": "do second",
                        "depends_on": ["n1"],
                        "ownership": ["claude_code/tools/agent/__init__.py"],
                    },
                ],
                "budget": {"max_parallelism": 2},
            },
        },
        context,
    )

    assert result.is_error is False
    content = str(result.content)
    assert "[supervisor:wf-agent] workflow smoke" in content
    assert "- n1 [completed]" in content
    assert "- n2 [completed]" in content
    assert "artifacts:" in content
    payload = content.split("artifacts:\n", 1)[1]
    artifacts = json.loads(payload)
    assert "n1" in artifacts and "n2" in artifacts
    assert "__bus__" in artifacts


@pytest.mark.asyncio
async def test_supervisor_artifact_flow_and_conflict_merge_failure():
    async def _executor(node, prompt, deps):
        if node.node_id == "a":
            return {
                "artifacts": [
                    {"type": "report", "key": "k", "content": "v1"},
                ]
            }
        if node.node_id == "b":
            # Default merge strategy is fail; same key should conflict.
            return {
                "artifacts": [
                    {"type": "report", "key": "k", "content": "v2"},
                ]
            }
        return {"artifacts": [{"type": "note", "key": "ok", "content": "fallback"}]}

    supervisor = MultiAgentSupervisor(executor=_executor, budget=SupervisorBudget(max_parallelism=1))
    nodes = [
        AgentNodeSpec(node_id="a", description="a", prompt="a"),
        AgentNodeSpec(node_id="b", description="b", prompt="b", dependencies=("a",)),
    ]
    result = await supervisor.run(workflow_id="wf-artifacts", nodes=nodes)
    by_id = {item.node_id: item for item in result.results}
    assert by_id["a"].status == NodeExecutionStatus.COMPLETED
    assert by_id["b"].status == NodeExecutionStatus.FAILED
    assert by_id["b"].error is not None and "artifact bus error" in by_id["b"].error
    assert "__bus__" in result.artifacts_by_node


@pytest.mark.asyncio
async def test_agent_tool_orchestrate_config_error_is_reported():
    tool = _FakeAgentTool()
    context = ToolContext(working_directory=".", environment={})

    result = await tool.execute(
        {
            "description": "broken workflow",
            "prompt": "root task",
            "orchestrate": True,
            "workflow": {"nodes": [{"id": "x", "description": "x"}]},
        },
        context,
    )
    assert result.is_error is True
    assert "Workflow config error" in str(result.content)

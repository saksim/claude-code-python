"""Runtime tests for AgentTool background/sync context inheritance consistency."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from claude_code.tasks.manager import TaskManager
from claude_code.tasks.queue import InMemoryTaskQueue
from claude_code.tools.agent import AgentTool
from claude_code.tools.base import ToolContext


class _FakeStreamEvent:
    def __init__(self, content: list[dict]) -> None:
        self.type = "message"
        self.content = {"content": content}
        self.usage = None
        self.error = None


class _FakeApiClient:
    async def create_message_streaming(self, messages, options):
        yield _FakeStreamEvent([{"type": "text", "text": "agent-ok"}])

    async def create_message(self, messages, options):
        return SimpleNamespace(content=[{"type": "text", "text": "agent-ok"}])


@pytest.mark.asyncio
async def test_agent_tool_sync_path_inherits_context_and_registry(monkeypatch):
    tool = AgentTool()
    fake_registry = object()

    captured: dict[str, object] = {}

    class _SpyQueryEngine:
        def __init__(self, api_client, config, tool_registry):
            captured["config"] = config
            captured["tool_registry"] = tool_registry

        async def query(self, prompt: str):
            yield {"type": "text", "content": "sync-ok"}

    monkeypatch.setattr("claude_code.main.setup_api_client", lambda cfg=None: _FakeApiClient())
    monkeypatch.setattr("claude_code.engine.query.QueryEngine", _SpyQueryEngine)

    context = ToolContext(
        working_directory="D:/workspace/main",
        environment={},
        permission_mode="plan",
        always_allow=["read"],
        always_deny=["write"],
        model="qwen2.5:14b",
        session_id="session-sync",
        conversation_id="conv-sync",
        memory_scope="local",
        api_provider="ollama",
        task_manager=TaskManager(task_queue=InMemoryTaskQueue()),
        tool_registry=fake_registry,
    )

    result = await tool.execute(
        {
            "description": "sync context check",
            "prompt": "verify sync context",
            "subagent_type": "general-purpose",
            "run_in_background": False,
            "cwd": "D:/workspace/sync-agent",
        },
        context,
    )

    assert result.is_error is False
    assert "sync-ok" in str(result.content)
    cfg = captured["config"]
    assert getattr(cfg, "working_directory") == "D:/workspace/sync-agent"
    assert getattr(cfg, "model") == "qwen2.5:14b"
    assert getattr(cfg, "permission_mode") == "plan"
    assert getattr(cfg, "memory_scope") == "project"
    assert captured["tool_registry"] is fake_registry


@pytest.mark.asyncio
async def test_agent_tool_background_path_inherits_context_and_task_metadata(monkeypatch):
    tool = AgentTool()
    manager = TaskManager(task_queue=InMemoryTaskQueue())
    fake_registry = object()

    captured: dict[str, object] = {}

    class _SpyQueryEngine:
        def __init__(self, api_client, config, tool_registry):
            captured["bg_config"] = config
            captured["bg_tool_registry"] = tool_registry

        async def query(self, prompt: str):
            yield {"type": "text", "content": "background-ok"}

    monkeypatch.setattr("claude_code.main.setup_api_client", lambda cfg=None: _FakeApiClient())
    monkeypatch.setattr("claude_code.engine.query.QueryEngine", _SpyQueryEngine)

    context = ToolContext(
        working_directory="D:/workspace/main",
        environment={},
        permission_mode="plan",
        always_allow=["read"],
        always_deny=["write"],
        model="qwen2.5:14b",
        session_id="session-bg",
        conversation_id="conv-bg",
        memory_scope="local",
        api_provider="ollama",
        task_manager=manager,
        tool_registry=fake_registry,
    )

    result = await tool.execute(
        {
            "description": "background context check",
            "prompt": "verify background context",
            "subagent_type": "general-purpose",
            "run_in_background": True,
            "cwd": "D:/workspace/bg-agent",
        },
        context,
    )

    assert result.is_error is False
    assert "Started background agent:" in str(result.content)

    tasks = manager.get_all_tasks()
    assert len(tasks) == 1
    task = tasks[0]
    assert task.metadata["session_id"] == "session-bg"
    assert task.metadata["conversation_id"] == "conv-bg"
    assert task.metadata["working_directory"] == "D:/workspace/bg-agent"
    assert task.metadata["permission_mode"] == "plan"
    assert task.metadata["memory_scope"] == "project"
    assert task.metadata["provider"] == "ollama"
    assert task.metadata["model"] == "qwen2.5:14b"
    assert task.metadata["source_tool"] == "agent"

    assert getattr(captured["bg_config"], "working_directory") == "D:/workspace/bg-agent"
    assert getattr(captured["bg_config"], "model") == "qwen2.5:14b"
    assert getattr(captured["bg_config"], "session_id") == "session-bg"
    assert getattr(captured["bg_config"], "permission_mode") == "plan"
    assert getattr(captured["bg_config"], "memory_scope") == "project"
    assert captured["bg_tool_registry"] is fake_registry

    await manager.wait_for_task(task.id, timeout=2.0)
    assert task.status.value == "completed"
    assert task.result is not None
    assert "background-ok" in task.result.stdout

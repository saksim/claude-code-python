"""Runtime tests for custom agents loader and AgentTool integration."""

from __future__ import annotations

import pytest
from claude_code.agents.loader import load_agents_from_directory
from claude_code.tools.agent import AgentTool
from claude_code.tools.base import ToolContext


def test_load_agents_from_directory_parses_and_overrides_nested_agents(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".git").mkdir()

    root_agents = root / ".claude" / "agents"
    root_agents.mkdir(parents=True)
    nested_agents = root / "sub" / ".claude" / "agents"
    nested_agents.mkdir(parents=True)

    (root_agents / "shared.md").write_text(
        "---\n"
        "name: shared\n"
        "description: root shared\n"
        "model: haiku\n"
        "tools:\n"
        "  - Read\n"
        "memory: user\n"
        "---\n"
        "root prompt\n",
        encoding="utf-8",
    )
    (nested_agents / "shared.md").write_text(
        "---\n"
        "name: shared\n"
        "description: nested shared\n"
        "model: sonnet\n"
        "tools:\n"
        "  - Bash\n"
        "disallowedTools:\n"
        "  - Edit\n"
        "memory: project\n"
        "---\n"
        "nested prompt\n",
        encoding="utf-8",
    )
    (nested_agents / "local-only.md").write_text(
        "---\n"
        "name: local-only\n"
        "description: nested only\n"
        "permissionMode: plan\n"
        "maxTurns: 2\n"
        "omitClaudeMd: true\n"
        "---\n"
        "local prompt\n",
        encoding="utf-8",
    )
    (nested_agents / "invalid.md").write_text(
        "no frontmatter content",
        encoding="utf-8",
    )

    loaded = load_agents_from_directory(root / "sub")

    assert "shared" in loaded
    assert "local-only" in loaded
    assert "invalid" not in loaded
    assert loaded["shared"].description == "nested shared"
    assert loaded["shared"].prompt == "nested prompt"
    assert loaded["shared"].model == "sonnet"
    assert loaded["shared"].tools == ["Bash"]
    assert loaded["shared"].disallowed_tools == ["Edit"]
    assert loaded["shared"].memory == "project"
    assert loaded["local-only"].permission_mode == "plan"
    assert loaded["local-only"].max_turns == 2
    assert loaded["local-only"].omit_claude_md is True


def test_load_agents_from_directory_handles_invalid_yaml_and_missing_required_fields(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".git").mkdir()
    agents_dir = root / ".claude" / "agents"
    agents_dir.mkdir(parents=True)

    (agents_dir / "broken-yaml.md").write_text(
        "---\n"
        "name: broken\n"
        "description: [unclosed\n"
        "---\n"
        "prompt\n",
        encoding="utf-8",
    )
    (agents_dir / "missing-description.md").write_text(
        "---\n"
        "name: missing\n"
        "---\n"
        "prompt\n",
        encoding="utf-8",
    )

    loaded = load_agents_from_directory(root)
    assert loaded == {}


@pytest.mark.asyncio
async def test_agent_tool_prefers_custom_agent_over_builtin_with_same_name(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".git").mkdir()
    agents_dir = root / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "general-purpose.md").write_text(
        "---\n"
        "name: general-purpose\n"
        "description: override default\n"
        "model: haiku\n"
        "memory: local\n"
        "---\n"
        "custom override prompt\n",
        encoding="utf-8",
    )

    tool = AgentTool()
    context = ToolContext(
        working_directory=str(root),
        environment={},
    )

    captured: dict[str, str] = {}

    async def _fake_run_sync_agent(*, agent_def, **kwargs):  # type: ignore[no-untyped-def]
        captured["agent_prompt"] = agent_def.prompt
        captured["agent_memory"] = str(agent_def.memory)
        captured["agent_model"] = agent_def.model
        from claude_code.tools.base import ToolResult

        return ToolResult(content="ok", is_error=False)

    monkeypatch.setattr(tool, "_run_sync_agent", _fake_run_sync_agent)

    result = await tool.execute(
        {
            "description": "run custom",
            "prompt": "test custom",
            "subagent_type": "general-purpose",
            "run_in_background": False,
        },
        context,
    )
    assert result.is_error is False
    assert captured["agent_prompt"] == "custom override prompt"
    assert captured["agent_memory"] == "local"
    assert captured["agent_model"] == "haiku"


@pytest.mark.asyncio
async def test_agent_tool_unknown_type_includes_custom_and_builtin_names(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".git").mkdir()
    agents_dir = root / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "my-custom.md").write_text(
        "---\n"
        "name: my-custom\n"
        "description: custom agent\n"
        "---\n"
        "custom prompt\n",
        encoding="utf-8",
    )

    tool = AgentTool()
    context = ToolContext(
        working_directory=str(root),
        environment={},
    )

    result = await tool.execute(
        {
            "description": "run unknown",
            "prompt": "test unknown",
            "subagent_type": "does-not-exist",
            "run_in_background": False,
        },
        context,
    )

    assert result.is_error is True
    message = str(result.content)
    assert "Unknown agent type: does-not-exist" in message
    assert "my-custom" in message
    assert "general-purpose" in message


def test_agent_tool_schema_allows_custom_subagent_type_names():
    tool = AgentTool()
    schema = tool.input_schema
    subagent_schema = schema["properties"]["subagent_type"]

    assert subagent_schema["type"] == "string"
    assert "enum" not in subagent_schema

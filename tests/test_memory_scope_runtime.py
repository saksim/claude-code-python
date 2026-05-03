"""Runtime tests for memory scope isolation contracts."""

from __future__ import annotations

import pytest

from claude_code.services.memory_service import MemoryEntry, SessionMemory


@pytest.mark.asyncio
async def test_session_memory_scope_isolation_between_user_project_local(tmp_path):
    memory = SessionMemory(storage_dir=tmp_path / "memory")

    await memory.set_scoped("user", "shared", "user-value", working_directory=tmp_path / "a")
    await memory.set_scoped("project", "shared", "project-a", working_directory=tmp_path / "a")
    await memory.set_scoped("project", "shared", "project-b", working_directory=tmp_path / "b")
    await memory.set_scoped("local", "shared", "local-a", working_directory=tmp_path / "a")

    assert await memory.get_scoped("user", "shared", working_directory=tmp_path / "a") == "user-value"
    assert await memory.get_scoped("user", "shared", working_directory=tmp_path / "b") == "user-value"
    assert await memory.get_scoped("project", "shared", working_directory=tmp_path / "a") == "project-a"
    assert await memory.get_scoped("project", "shared", working_directory=tmp_path / "b") == "project-b"
    assert await memory.get_scoped("local", "shared", working_directory=tmp_path / "a") == "local-a"
    assert await memory.get_scoped("local", "shared", working_directory=tmp_path / "b") is None


def test_snapshot_scoped_uses_scope_boundaries(tmp_path):
    memory = SessionMemory(storage_dir=tmp_path / "memory")
    project_a = tmp_path / "project-a"
    project_b = tmp_path / "project-b"

    key_a = SessionMemory._scoped_key("project", "k1", working_directory=project_a)
    key_b = SessionMemory._scoped_key("project", "k2", working_directory=project_b)
    key_user = SessionMemory._scoped_key("user", "k3", working_directory=project_a)

    memory._memory[key_a] = MemoryEntry(key=key_a, value="A")  # type: ignore[attr-defined]
    memory._memory[key_b] = MemoryEntry(key=key_b, value="B")  # type: ignore[attr-defined]
    memory._memory[key_user] = MemoryEntry(key=key_user, value="U")  # type: ignore[attr-defined]

    snap_a = memory.snapshot_scoped("project", working_directory=project_a)
    snap_b = memory.snapshot_scoped("project", working_directory=project_b)
    snap_user = memory.snapshot_scoped("user", working_directory=project_a)

    assert snap_a == {"k1": "A"}
    assert snap_b == {"k2": "B"}
    assert snap_user == {"k3": "U"}

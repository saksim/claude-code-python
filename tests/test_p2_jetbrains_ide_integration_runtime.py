"""Runtime tests for P2-10 JetBrains IDE integration adapter."""

from __future__ import annotations

from pathlib import Path

from claude_code.server.ide_adapter import JetBrainsClientAdapter


def test_jetbrains_client_adapter_normalizes_workspace_snapshot(tmp_path: Path):
    class _FakeDaemonClient:
        def get_ide_workspace(self, **kwargs):
            assert kwargs["include_diff"] is True
            return {
                "workspace": {
                    "working_directory": str(tmp_path),
                    "diff": {
                        "content": "diff --git a/a.py b/a.py",
                        "truncated": False,
                        "line_count": 1,
                    },
                    "changed_files": [{"path": "a.py", "status": " M"}],
                    "sessions": [{"id": "session-1"}],
                    "tasks": [{"id": "task-1"}],
                    "findings": [
                        {
                            "file_path": "a.py",
                            "line": "12",
                            "severity": "high",
                            "issue": "unsafe call",
                            "recommendation": "guard input",
                        },
                        {
                            "file_path": "b.py",
                            "line": 8,
                            "severity": "low",
                            "issue": "style drift",
                            "recommendation": "align naming",
                        },
                    ],
                }
            }

    adapter = JetBrainsClientAdapter(_FakeDaemonClient())  # type: ignore[arg-type]
    snapshot = adapter.fetch_workspace_snapshot()

    assert snapshot.project_root == str(tmp_path)
    assert snapshot.vcs["diff"]["content"].startswith("diff --git")
    assert snapshot.vcs["changed_files"][0]["path"] == "a.py"
    assert snapshot.sessions[0]["id"] == "session-1"
    assert snapshot.tasks[0]["id"] == "task-1"

    assert snapshot.inspections[0]["file_path"] == "a.py"
    assert snapshot.inspections[0]["line"] == 12
    assert snapshot.inspections[0]["highlight"] == "error"
    assert snapshot.inspections[1]["highlight"] == "weak_warning"


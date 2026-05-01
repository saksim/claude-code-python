"""Phase 1 card P1-05 gate runner for hook/permission/audit convergence.

This script only defines Linux-stage test command list and does not run tests.
"""

from __future__ import annotations

from pathlib import Path


def build_gate_commands(project_root: Path) -> list[str]:
    return [
        "python -m pytest -q -c pytest.ini tests/test_permissions_unified.py",
        "python -m pytest -q -c pytest.ini tests/test_hooks_runtime.py",
        "python -m pytest -q -c pytest.ini tests/test_event_journal_runtime.py",
        "python -m pytest -q -c pytest.ini tests/test_query_engine_runtime.py",
        "python -m pytest -q -c pytest.ini tests/test_hook_permission_audit_runtime.py",
        "python -m pytest -q -c pytest.ini tests/test_main_runtime.py",
        "python -m pytest -q -c pytest.ini tests/test_server_runtime.py",
    ]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    commands = build_gate_commands(root)
    print("P1-05 hook/permission/audit gate commands (Linux execution stage):")
    for idx, command in enumerate(commands, start=1):
        print(f"{idx}. {command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

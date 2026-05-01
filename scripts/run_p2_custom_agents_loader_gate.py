"""Phase 2 card P2-08 gate runner for custom agents loader/runtime chain.

This script only defines Linux-stage test command list and does not run tests.
"""

from __future__ import annotations

from pathlib import Path


def build_gate_commands(project_root: Path) -> list[str]:
    _ = project_root
    return [
        "python -m pytest -q -c pytest.ini tests/test_custom_agents_loader_runtime.py",
        "python -m pytest -q -c pytest.ini tests/test_agent_background_context_runtime.py",
        "python -m pytest -q -c pytest.ini tests/test_main_runtime.py",
    ]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    commands = build_gate_commands(root)
    print("P2-08 custom agents loader gate commands (Linux execution stage):")
    for idx, command in enumerate(commands, start=1):
        print(f"{idx}. {command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


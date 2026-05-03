"""Phase 2 card P2-10 gate runner for JetBrains IDE integration.

This script only defines Linux-stage test command list and does not run tests.
"""

from __future__ import annotations

from pathlib import Path


def build_gate_commands(project_root: Path) -> list[str]:
    return [
        "python -m pytest -q -c pytest.ini tests/test_p2_jetbrains_ide_integration_runtime.py",
        "python -m pytest -q -c pytest.ini tests/test_ide_integration_runtime.py",
        "python -m pytest -q -c pytest.ini tests/test_server_runtime.py",
        "python -m pytest -q -c pytest.ini tests/test_main_runtime.py",
    ]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    commands = build_gate_commands(root)
    print("P2-10 JetBrains IDE integration gate commands (Linux execution stage):")
    for idx, command in enumerate(commands, start=1):
        print(f"{idx}. {command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


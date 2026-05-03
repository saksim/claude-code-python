"""Contract tests for P2-10 JetBrains IDE integration gate script."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_p2_jetbrains_ide_integration_gate_module():
    script_path = Path("scripts") / "run_p2_jetbrains_ide_integration_gate.py"
    spec = importlib.util.spec_from_file_location("p2_jetbrains_ide_integration_gate", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_p2_jetbrains_ide_integration_gate_contract():
    gate = _load_p2_jetbrains_ide_integration_gate_module()
    commands = gate.build_gate_commands(Path.cwd())

    assert len(commands) == 4
    assert commands[0] == (
        "python -m pytest -q -c pytest.ini tests/test_p2_jetbrains_ide_integration_runtime.py"
    )
    assert commands[-1] == "python -m pytest -q -c pytest.ini tests/test_main_runtime.py"
    for command in commands:
        assert command.startswith("python -m pytest -q -c pytest.ini ")
        test_file = command.split("pytest.ini ", 1)[1]
        assert Path(test_file).is_file()

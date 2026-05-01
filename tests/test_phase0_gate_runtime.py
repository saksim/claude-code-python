"""Contract tests for Phase 0 regression gate script."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_phase0_gate_module():
    script_path = Path("scripts") / "run_phase0_gate.py"
    spec = importlib.util.spec_from_file_location("phase0_gate", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_phase0_gate_manifest_references_existing_files():
    gate = _load_phase0_gate_module()
    assert gate.PHASE0_GATE_TEST_FILES
    for test_file in gate.PHASE0_GATE_TEST_FILES:
        assert Path(test_file).is_file()


def test_phase0_gate_builds_pytest_command_contract():
    gate = _load_phase0_gate_module()
    command = gate.build_phase0_pytest_command(
        python_executable="python-custom",
        extra_pytest_args=["-k", "phase0", "--maxfail", "1"],
    )

    assert command[:5] == ["python-custom", "-m", "pytest", "-c", "pytest.ini"]
    assert command[5 : 5 + len(gate.PHASE0_GATE_TEST_FILES)] == list(
        gate.PHASE0_GATE_TEST_FILES
    )
    assert command[-4:] == ["-k", "phase0", "--maxfail", "1"]

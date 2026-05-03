"""Contract tests for Phase 0 regression gate organization."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


pytestmark = pytest.mark.phase0_gate


def _load_phase0_gate_module():
    script_path = Path("scripts") / "run_phase0_gate.py"
    spec = importlib.util.spec_from_file_location("phase0_gate_script", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_phase0_gate_manifest_references_existing_test_files():
    gate = _load_phase0_gate_module()
    assert gate.PHASE0_GATE_TEST_FILES
    for test_file in gate.PHASE0_GATE_TEST_FILES:
        assert Path(test_file).is_file()


def test_phase0_gate_build_command_contains_pytest_ini_and_manifest_files():
    gate = _load_phase0_gate_module()
    command = gate.build_phase0_pytest_command(
        python_executable="python-custom",
        extra_pytest_args=["-k", "runtime"],
    )

    assert command[:5] == ["python-custom", "-m", "pytest", "-c", "pytest.ini"]
    for test_file in gate.PHASE0_GATE_TEST_FILES:
        assert test_file in command
    assert command[-2:] == ["-k", "runtime"]


def test_phase0_gate_marker_registered_in_pytest_ini():
    content = Path("pytest.ini").read_text(encoding="utf-8")
    assert "phase0_gate:" in content

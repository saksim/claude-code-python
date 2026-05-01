"""Contract tests for P1-01 control-plane gate script."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_p1_control_plane_gate_module():
    script_path = Path("scripts") / "run_p1_control_plane_gate.py"
    spec = importlib.util.spec_from_file_location("p1_control_plane_gate", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_p1_control_plane_gate_manifest_references_existing_files():
    gate = _load_p1_control_plane_gate_module()
    assert gate.P1_CONTROL_PLANE_TEST_FILES
    for test_file in gate.P1_CONTROL_PLANE_TEST_FILES:
        assert Path(test_file).is_file()


def test_p1_control_plane_gate_builds_pytest_command_contract():
    gate = _load_p1_control_plane_gate_module()
    command = gate.build_p1_control_plane_pytest_command(
        python_executable="python-custom",
        extra_pytest_args=["-k", "daemon", "--maxfail", "1"],
    )

    assert command[:5] == ["python-custom", "-m", "pytest", "-c", "pytest.ini"]
    for test_file in gate.P1_CONTROL_PLANE_TEST_FILES:
        assert test_file in command
    assert command[-4:] == ["-k", "daemon", "--maxfail", "1"]

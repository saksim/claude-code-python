"""Contract tests for Linux unified gate command manifest."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_linux_unified_gate_module():
    script_path = Path("scripts") / "run_linux_unified_gate.py"
    spec = importlib.util.spec_from_file_location("linux_unified_gate_script", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_linux_unified_gate_manifest_references_existing_test_files():
    gate = _load_linux_unified_gate_module()
    assert gate.LINUX_UNIFIED_TEST_FILES
    for test_file in gate.LINUX_UNIFIED_TEST_FILES:
        assert Path(test_file).is_file()


def test_linux_unified_gate_command_list_matches_manifest_order():
    gate = _load_linux_unified_gate_module()
    commands = gate.build_gate_commands(Path.cwd())

    assert len(commands) == len(gate.LINUX_UNIFIED_TEST_FILES)
    expected_prefix = "python -m pytest -q -c pytest.ini "
    for idx, test_file in enumerate(gate.LINUX_UNIFIED_TEST_FILES):
        assert commands[idx] == f"{expected_prefix}{test_file}"


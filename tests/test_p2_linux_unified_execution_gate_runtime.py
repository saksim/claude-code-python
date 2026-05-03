"""Contract tests for P2-09 Linux unified execution gate."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_execution_gate_module():
    script_path = Path("scripts") / "run_p2_linux_unified_execution_gate.py"
    spec = importlib.util.spec_from_file_location("p2_linux_unified_execution_gate", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_unified_manifest_module():
    script_path = Path("scripts") / "run_linux_unified_gate.py"
    spec = importlib.util.spec_from_file_location("linux_unified_gate_script", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_p2_linux_unified_execution_gate_tracks_unified_manifest():
    gate = _load_execution_gate_module()
    manifest = _load_unified_manifest_module()

    test_files = tuple(manifest.LINUX_UNIFIED_TEST_FILES)
    report_dir = Path("tmp/report")
    commands = gate.build_gate_commands(
        python_executable="python-custom",
        test_files=test_files,
        report_dir=report_dir,
        extra_pytest_args=None,
    )

    assert len(commands) == len(test_files)
    assert commands
    for idx, test_file in enumerate(test_files):
        command = commands[idx]
        assert command[:6] == ["python-custom", "-m", "pytest", "-q", "-c", "pytest.ini"]
        assert command[6] == test_file
        assert command[7:9] == ["--junitxml", str(report_dir / f"{Path(test_file).stem}.xml")]


def test_p2_linux_unified_execution_gate_applies_extra_pytest_args():
    gate = _load_execution_gate_module()
    commands = gate.build_gate_commands(
        python_executable="python",
        test_files=["tests/test_main_runtime.py"],
        report_dir=Path("tmp/report"),
        extra_pytest_args=["-k", "daemon", "--maxfail", "1"],
    )

    assert len(commands) == 1
    assert commands[0][-4:] == ["-k", "daemon", "--maxfail", "1"]


def test_p2_linux_unified_execution_gate_selects_deterministic_shard_slice():
    gate = _load_execution_gate_module()
    files = [
        "tests/a.py",
        "tests/b.py",
        "tests/c.py",
        "tests/d.py",
        "tests/e.py",
    ]

    shard_1 = gate.select_shard_test_files(files, shard_total=3, shard_index=1)
    shard_2 = gate.select_shard_test_files(files, shard_total=3, shard_index=2)
    shard_3 = gate.select_shard_test_files(files, shard_total=3, shard_index=3)

    assert shard_1 == ["tests/a.py", "tests/d.py"]
    assert shard_2 == ["tests/b.py", "tests/e.py"]
    assert shard_3 == ["tests/c.py"]


def test_p2_linux_unified_execution_gate_rejects_invalid_shard_arguments():
    gate = _load_execution_gate_module()
    files = ["tests/a.py"]

    try:
        gate.select_shard_test_files(files, shard_total=0, shard_index=1)
        raised_total = False
    except ValueError:
        raised_total = True

    try:
        gate.select_shard_test_files(files, shard_total=2, shard_index=3)
        raised_index = False
    except ValueError:
        raised_index = True

    assert raised_total
    assert raised_index


def test_p2_linux_unified_execution_gate_summary_includes_shard_metadata():
    gate = _load_execution_gate_module()
    payload = gate._build_result_payload(
        python_executable="python",
        report_dir=Path("tmp/report"),
        manifest_test_files=["tests/a.py", "tests/b.py", "tests/c.py"],
        selected_test_files=["tests/a.py", "tests/c.py"],
        shard_total=2,
        shard_index=1,
        commands=[["python", "-m", "pytest", "tests/a.py"]],
        per_test_status=[{"test_file": "tests/a.py", "exit_code": 0, "junit_xml": "tmp/a.xml"}],
    )

    assert payload["manifest_total_tests"] == 3
    assert payload["total_tests"] == 2
    assert payload["shard_total"] == 2
    assert payload["shard_index"] == 1


def test_p2_linux_unified_execution_gate_empty_shard_summary_contract():
    gate = _load_execution_gate_module()
    payload = gate._build_result_payload(
        python_executable="python",
        report_dir=Path("tmp/report"),
        manifest_test_files=["tests/a.py", "tests/b.py"],
        selected_test_files=[],
        shard_total=3,
        shard_index=3,
        commands=[],
        per_test_status=[],
    )

    assert payload["manifest_total_tests"] == 2
    assert payload["total_tests"] == 0
    assert payload["passed"] == 0
    assert payload["failed"] == 0
    assert payload["shard_total"] == 3
    assert payload["shard_index"] == 3

"""Contract tests for P2-15 Linux shard plan gate."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_shard_plan_gate_module():
    script_path = Path("scripts") / "run_p2_linux_shard_plan_gate.py"
    spec = importlib.util.spec_from_file_location("p2_linux_shard_plan_gate", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_shard_plan_payload_distributes_tests_deterministically():
    gate = _load_shard_plan_gate_module()
    payload = gate.build_shard_plan_payload(
        python_executable="python",
        test_files=["tests/a.py", "tests/b.py", "tests/c.py", "tests/d.py", "tests/e.py"],
        shard_total=3,
        report_root=Path(".claude/reports/linux_unified_gate/shards"),
        continue_on_failure=False,
        pytest_args=None,
    )

    assert payload["manifest_total_tests"] == 5
    assert payload["shard_total"] == 3
    assert len(payload["shards"]) == 3

    assert payload["shards"][0]["test_files"] == ["tests/a.py", "tests/d.py"]
    assert payload["shards"][1]["test_files"] == ["tests/b.py", "tests/e.py"]
    assert payload["shards"][2]["test_files"] == ["tests/c.py"]


def test_build_shard_plan_payload_command_contract_includes_forwarded_args():
    gate = _load_shard_plan_gate_module()
    payload = gate.build_shard_plan_payload(
        python_executable="python3",
        test_files=["tests/a.py"],
        shard_total=1,
        report_root=Path("reports/shards"),
        continue_on_failure=True,
        pytest_args=["-k", "daemon", "--maxfail", "1"],
    )

    shard = payload["shards"][0]
    assert shard["command_parts"][:2] == ["python3", "scripts/run_p2_linux_unified_execution_gate.py"]
    assert "--continue-on-failure" in shard["command_parts"]
    assert "--" in shard["command_parts"]
    assert shard["command_parts"][-4:] == ["-k", "daemon", "--maxfail", "1"]
    assert shard["summary_path"].endswith("shard-1/summary.json")


def test_build_shard_plan_payload_rejects_invalid_shard_total():
    gate = _load_shard_plan_gate_module()
    try:
        gate.build_shard_plan_payload(
            python_executable="python",
            test_files=["tests/a.py"],
            shard_total=0,
            report_root=Path("reports/shards"),
            continue_on_failure=False,
            pytest_args=[],
        )
        raised = False
    except ValueError:
        raised = True

    assert raised

"""Contract tests for P2-16 Linux CI matrix gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_matrix_gate_module():
    script_path = Path("scripts") / "run_p2_linux_ci_matrix_gate.py"
    spec = importlib.util.spec_from_file_location("p2_linux_ci_matrix_gate", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_shard_plan():
    return {
        "manifest_total_tests": 5,
        "shard_total": 3,
        "shards": [
            {
                "shard_index": 1,
                "shard_total": 3,
                "total_tests": 2,
                "test_files": ["tests/a.py", "tests/d.py"],
                "report_dir": ".claude/reports/linux_unified_gate/shards/shard-1",
                "summary_path": ".claude/reports/linux_unified_gate/shards/shard-1/summary.json",
                "command": "python scripts/run_p2_linux_unified_execution_gate.py --shard-total 3 --shard-index 1",
                "command_parts": [
                    "python",
                    "scripts/run_p2_linux_unified_execution_gate.py",
                    "--shard-total",
                    "3",
                    "--shard-index",
                    "1",
                ],
            },
            {
                "shard_index": 2,
                "shard_total": 3,
                "total_tests": 2,
                "test_files": ["tests/b.py", "tests/e.py"],
                "report_dir": ".claude/reports/linux_unified_gate/shards/shard-2",
                "summary_path": ".claude/reports/linux_unified_gate/shards/shard-2/summary.json",
                "command": "python scripts/run_p2_linux_unified_execution_gate.py --shard-total 3 --shard-index 2",
                "command_parts": [
                    "python",
                    "scripts/run_p2_linux_unified_execution_gate.py",
                    "--shard-total",
                    "3",
                    "--shard-index",
                    "2",
                ],
            },
            {
                "shard_index": 3,
                "shard_total": 3,
                "total_tests": 1,
                "test_files": ["tests/c.py"],
                "report_dir": ".claude/reports/linux_unified_gate/shards/shard-3",
                "summary_path": ".claude/reports/linux_unified_gate/shards/shard-3/summary.json",
                "command": "python scripts/run_p2_linux_unified_execution_gate.py --shard-total 3 --shard-index 3",
                "command_parts": [
                    "python",
                    "scripts/run_p2_linux_unified_execution_gate.py",
                    "--shard-total",
                    "3",
                    "--shard-index",
                    "3",
                ],
            },
        ],
    }


def test_build_ci_matrix_payload_preserves_shard_order_and_fields():
    gate = _load_ci_matrix_gate_module()
    payload = gate.build_ci_matrix_payload(
        _sample_shard_plan(),
        source_path=Path("reports/shard_plan.json"),
        skip_empty_shards=False,
    )

    include = payload["matrix"]["include"]
    assert payload["selected_shards"] == 3
    assert [item["shard_index"] for item in include] == [1, 2, 3]
    assert include[0]["command_parts"][-2:] == ["--shard-index", "1"]
    assert payload["summary_paths"][2].endswith("shard-3/summary.json")


def test_build_ci_matrix_payload_skip_empty_shards_contract():
    gate = _load_ci_matrix_gate_module()
    shard_plan = _sample_shard_plan()
    shard_plan["manifest_total_tests"] = 4
    shard_plan["shards"][2]["total_tests"] = 0
    shard_plan["shards"][2]["test_files"] = []

    payload = gate.build_ci_matrix_payload(
        shard_plan,
        source_path=Path("reports/shard_plan.json"),
        skip_empty_shards=True,
    )

    include = payload["matrix"]["include"]
    assert payload["selected_shards"] == 2
    assert [item["shard_index"] for item in include] == [1, 2]
    assert all(item["total_tests"] > 0 for item in include)


def test_build_github_output_values_contract():
    gate = _load_ci_matrix_gate_module()
    payload = gate.build_ci_matrix_payload(
        _sample_shard_plan(),
        source_path=Path("reports/shard_plan.json"),
        skip_empty_shards=False,
    )

    outputs = gate.build_github_output_values(payload)
    assert "matrix" in outputs
    assert "summary_paths" in outputs
    assert outputs["selected_shards"] == "3"
    assert outputs["shard_total"] == "3"


def test_load_shard_plan_rejects_total_mismatch(tmp_path: Path):
    gate = _load_ci_matrix_gate_module()
    bad_plan = _sample_shard_plan()
    bad_plan["manifest_total_tests"] = 6
    path = tmp_path / "bad_shard_plan.json"
    path.write_text(json.dumps(bad_plan), encoding="utf-8")

    try:
        gate.load_shard_plan(path)
        raised = False
    except ValueError:
        raised = True

    assert raised

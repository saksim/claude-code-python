"""Contract tests for P2-17 Linux CI workflow plan gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_plan_gate_module():
    script_path = Path("scripts") / "run_p2_linux_ci_workflow_plan_gate.py"
    spec = importlib.util.spec_from_file_location("p2_linux_ci_workflow_plan_gate", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_ci_matrix() -> dict:
    return {
        "generated_at": "2026-04-30T00:00:00+00:00",
        "source_shard_plan": "/tmp/shard_plan.json",
        "shard_total": 3,
        "manifest_total_tests": 5,
        "selected_shards": 3,
        "skipped_empty_shards": False,
        "matrix": {
            "include": [
                {
                    "shard_index": 1,
                    "shard_total": 3,
                    "total_tests": 2,
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
            ]
        },
        "summary_paths": [
            ".claude/reports/linux_unified_gate/shards/shard-1/summary.json",
            ".claude/reports/linux_unified_gate/shards/shard-2/summary.json",
            ".claude/reports/linux_unified_gate/shards/shard-3/summary.json",
        ],
    }


def test_build_ci_workflow_plan_payload_fan_out_and_fan_in_contract():
    gate = _load_ci_workflow_plan_gate_module()
    payload = gate.build_ci_workflow_plan_payload(
        _sample_ci_matrix(),
        source_path=Path("reports/ci_matrix.json"),
        python_executable="python3",
        merged_summary_output=Path("reports/merged_summary.json"),
        final_report_json=Path("reports/final_report.json"),
        final_report_markdown=Path("reports/final_report.md"),
    )

    assert payload["selected_shards"] == 3
    assert len(payload["fan_out_jobs"]) == 3
    assert payload["fan_out_jobs"][0]["job_id"] == "linux-shard-1"
    assert payload["fan_out_jobs"][2]["summary_path"].endswith("shard-3/summary.json")

    aggregation_parts = payload["fan_in"]["aggregation_command_parts"]
    assert aggregation_parts[:2] == ["python3", "scripts/run_p2_linux_shard_aggregation_gate.py"]
    assert "--summary" in aggregation_parts
    publish_parts = payload["fan_in"]["publish_command_parts"]
    assert publish_parts[:2] == ["python3", "scripts/run_p2_linux_report_publish_gate.py"]
    assert "--merged-summary" in publish_parts


def test_build_github_output_values_contract():
    gate = _load_ci_workflow_plan_gate_module()
    payload = gate.build_ci_workflow_plan_payload(
        _sample_ci_matrix(),
        source_path=Path("reports/ci_matrix.json"),
        python_executable="python",
        merged_summary_output=Path("reports/merged_summary.json"),
        final_report_json=Path("reports/final_report.json"),
        final_report_markdown=Path("reports/final_report.md"),
    )

    outputs = gate.build_github_output_values(payload)
    assert "fan_out_matrix" in outputs
    assert "fan_in_summary_paths" in outputs
    assert "aggregation_command" in outputs
    assert "publish_command" in outputs
    assert outputs["selected_shards"] == "3"
    assert outputs["manifest_total_tests"] == "5"


def test_load_ci_matrix_rejects_summary_order_mismatch(tmp_path: Path):
    gate = _load_ci_workflow_plan_gate_module()
    payload = _sample_ci_matrix()
    payload["summary_paths"] = list(reversed(payload["summary_paths"]))
    matrix_path = tmp_path / "ci_matrix_bad.json"
    matrix_path.write_text(json.dumps(payload), encoding="utf-8")

    try:
        gate.load_ci_matrix(matrix_path)
        raised = False
    except ValueError:
        raised = True

    assert raised


def test_load_ci_matrix_rejects_selected_shards_mismatch(tmp_path: Path):
    gate = _load_ci_workflow_plan_gate_module()
    payload = _sample_ci_matrix()
    payload["selected_shards"] = 2
    matrix_path = tmp_path / "ci_matrix_bad_selected.json"
    matrix_path.write_text(json.dumps(payload), encoding="utf-8")

    try:
        gate.load_ci_matrix(matrix_path)
        raised = False
    except ValueError:
        raised = True

    assert raised

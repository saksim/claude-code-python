"""Contract tests for P2-20 Linux CI workflow command guard gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_command_guard_gate_module():
    script_path = Path("scripts") / "run_p2_linux_ci_workflow_command_guard_gate.py"
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_command_guard_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_ci_workflow_plan() -> dict:
    return {
        "generated_at": "2026-04-30T00:00:00+00:00",
        "source_ci_matrix": "/tmp/ci_matrix.json",
        "shard_total": 2,
        "manifest_total_tests": 4,
        "selected_shards": 2,
        "skipped_empty_shards": False,
        "fan_out_matrix": {
            "include": [
                {
                    "job_id": "linux-shard-1",
                    "shard_index": 1,
                    "shard_total": 2,
                    "total_tests": 2,
                    "report_dir": ".claude/reports/linux_unified_gate/shards/shard-1",
                    "summary_path": ".claude/reports/linux_unified_gate/shards/shard-1/summary.json",
                    "command": "python scripts/run_p2_linux_unified_execution_gate.py --report-dir .claude/reports/linux_unified_gate/shards/shard-1 --shard-total 2 --shard-index 1 --continue-on-failure",
                    "command_parts": [
                        "python",
                        "scripts/run_p2_linux_unified_execution_gate.py",
                        "--report-dir",
                        ".claude/reports/linux_unified_gate/shards/shard-1",
                        "--shard-total",
                        "2",
                        "--shard-index",
                        "1",
                        "--continue-on-failure",
                    ],
                },
                {
                    "job_id": "linux-shard-2",
                    "shard_index": 2,
                    "shard_total": 2,
                    "total_tests": 2,
                    "report_dir": ".claude/reports/linux_unified_gate/shards/shard-2",
                    "summary_path": ".claude/reports/linux_unified_gate/shards/shard-2/summary.json",
                    "command": "python scripts/run_p2_linux_unified_execution_gate.py --report-dir .claude/reports/linux_unified_gate/shards/shard-2 --shard-total 2 --shard-index 2 --continue-on-failure",
                    "command_parts": [
                        "python",
                        "scripts/run_p2_linux_unified_execution_gate.py",
                        "--report-dir",
                        ".claude/reports/linux_unified_gate/shards/shard-2",
                        "--shard-total",
                        "2",
                        "--shard-index",
                        "2",
                        "--continue-on-failure",
                    ],
                },
            ]
        },
        "fan_out_jobs": [
            {
                "job_id": "linux-shard-1",
                "shard_index": 1,
                "shard_total": 2,
                "total_tests": 2,
                "report_dir": ".claude/reports/linux_unified_gate/shards/shard-1",
                "summary_path": ".claude/reports/linux_unified_gate/shards/shard-1/summary.json",
                "command": "python scripts/run_p2_linux_unified_execution_gate.py --report-dir .claude/reports/linux_unified_gate/shards/shard-1 --shard-total 2 --shard-index 1 --continue-on-failure",
                "command_parts": [
                    "python",
                    "scripts/run_p2_linux_unified_execution_gate.py",
                    "--report-dir",
                    ".claude/reports/linux_unified_gate/shards/shard-1",
                    "--shard-total",
                    "2",
                    "--shard-index",
                    "1",
                    "--continue-on-failure",
                ],
            },
            {
                "job_id": "linux-shard-2",
                "shard_index": 2,
                "shard_total": 2,
                "total_tests": 2,
                "report_dir": ".claude/reports/linux_unified_gate/shards/shard-2",
                "summary_path": ".claude/reports/linux_unified_gate/shards/shard-2/summary.json",
                "command": "python scripts/run_p2_linux_unified_execution_gate.py --report-dir .claude/reports/linux_unified_gate/shards/shard-2 --shard-total 2 --shard-index 2 --continue-on-failure",
                "command_parts": [
                    "python",
                    "scripts/run_p2_linux_unified_execution_gate.py",
                    "--report-dir",
                    ".claude/reports/linux_unified_gate/shards/shard-2",
                    "--shard-total",
                    "2",
                    "--shard-index",
                    "2",
                    "--continue-on-failure",
                ],
            },
        ],
        "fan_in": {
            "summary_paths": [
                ".claude/reports/linux_unified_gate/shards/shard-1/summary.json",
                ".claude/reports/linux_unified_gate/shards/shard-2/summary.json",
            ],
            "merged_summary_path": ".claude/reports/linux_unified_gate/merged_summary.json",
            "aggregation_command": "python scripts/run_p2_linux_shard_aggregation_gate.py --output .claude/reports/linux_unified_gate/merged_summary.json --summary .claude/reports/linux_unified_gate/shards/shard-1/summary.json --summary .claude/reports/linux_unified_gate/shards/shard-2/summary.json",
            "aggregation_command_parts": [
                "python",
                "scripts/run_p2_linux_shard_aggregation_gate.py",
                "--output",
                ".claude/reports/linux_unified_gate/merged_summary.json",
                "--summary",
                ".claude/reports/linux_unified_gate/shards/shard-1/summary.json",
                "--summary",
                ".claude/reports/linux_unified_gate/shards/shard-2/summary.json",
            ],
            "publish_command": "python scripts/run_p2_linux_report_publish_gate.py --merged-summary .claude/reports/linux_unified_gate/merged_summary.json --output-json .claude/reports/linux_unified_gate/final_report.json --output-markdown .claude/reports/linux_unified_gate/final_report.md",
            "publish_command_parts": [
                "python",
                "scripts/run_p2_linux_report_publish_gate.py",
                "--merged-summary",
                ".claude/reports/linux_unified_gate/merged_summary.json",
                "--output-json",
                ".claude/reports/linux_unified_gate/final_report.json",
                "--output-markdown",
                ".claude/reports/linux_unified_gate/final_report.md",
            ],
            "final_report_json": ".claude/reports/linux_unified_gate/final_report.json",
            "final_report_markdown": ".claude/reports/linux_unified_gate/final_report.md",
        },
    }


def test_guard_ci_workflow_plan_commands_passes_on_valid_payload():
    gate = _load_ci_workflow_command_guard_gate_module()
    plan = _sample_ci_workflow_plan()

    normalized_plan, report = gate.guard_ci_workflow_plan_commands(plan)

    assert report["overall_status"] == "passed"
    assert report["failed_commands"] == 0
    assert report["issues"] == []
    assert normalized_plan["fan_in"]["aggregation_command"] == plan["fan_in"]["aggregation_command"]


def test_guard_detects_command_parts_mismatch_and_returns_normalized_command():
    gate = _load_ci_workflow_command_guard_gate_module()
    plan = _sample_ci_workflow_plan()

    plan["fan_out_matrix"]["include"][0]["command"] = (
        "python scripts/run_p2_linux_unified_execution_gate.py --report-dir "
        ".claude/reports/linux_unified_gate/shards/shard-1 --shard-total 2 "
        "--shard-index 1 --continue-on-failure --dry-run"
    )

    normalized_plan, report = gate.guard_ci_workflow_plan_commands(plan)

    assert report["overall_status"] == "failed"
    issue_codes = [item["code"] for item in report["issues"]]
    assert "command_parts_mismatch" in issue_codes
    assert normalized_plan["fan_out_matrix"]["include"][0]["command"] == (
        "python scripts/run_p2_linux_unified_execution_gate.py --report-dir "
        ".claude/reports/linux_unified_gate/shards/shard-1 --shard-total 2 "
        "--shard-index 1 --continue-on-failure"
    )


def test_guard_detects_aggregation_summary_paths_mismatch():
    gate = _load_ci_workflow_command_guard_gate_module()
    plan = _sample_ci_workflow_plan()

    plan["fan_in"]["aggregation_command_parts"] = [
        "python",
        "scripts/run_p2_linux_shard_aggregation_gate.py",
        "--output",
        ".claude/reports/linux_unified_gate/merged_summary.json",
        "--summary",
        ".claude/reports/linux_unified_gate/shards/shard-2/summary.json",
        "--summary",
        ".claude/reports/linux_unified_gate/shards/shard-1/summary.json",
    ]
    plan["fan_in"]["aggregation_command"] = (
        "python scripts/run_p2_linux_shard_aggregation_gate.py --output "
        ".claude/reports/linux_unified_gate/merged_summary.json --summary "
        ".claude/reports/linux_unified_gate/shards/shard-2/summary.json --summary "
        ".claude/reports/linux_unified_gate/shards/shard-1/summary.json"
    )

    _, report = gate.guard_ci_workflow_plan_commands(plan)

    assert report["overall_status"] == "failed"
    issue_codes = [item["code"] for item in report["issues"]]
    assert "summary_paths_mismatch" in issue_codes


def test_guard_detects_publish_report_path_mismatch():
    gate = _load_ci_workflow_command_guard_gate_module()
    plan = _sample_ci_workflow_plan()

    plan["fan_in"]["publish_command_parts"] = [
        "python",
        "scripts/run_p2_linux_report_publish_gate.py",
        "--merged-summary",
        ".claude/reports/linux_unified_gate/merged_summary.json",
        "--output-json",
        ".claude/reports/linux_unified_gate/final_report-alt.json",
        "--output-markdown",
        ".claude/reports/linux_unified_gate/final_report.md",
    ]
    plan["fan_in"]["publish_command"] = (
        "python scripts/run_p2_linux_report_publish_gate.py --merged-summary "
        ".claude/reports/linux_unified_gate/merged_summary.json --output-json "
        ".claude/reports/linux_unified_gate/final_report-alt.json --output-markdown "
        ".claude/reports/linux_unified_gate/final_report.md"
    )

    _, report = gate.guard_ci_workflow_plan_commands(plan)

    assert report["overall_status"] == "failed"
    issue_codes = [item["code"] for item in report["issues"]]
    assert "publish_output_json_mismatch" in issue_codes


def test_load_ci_workflow_plan_rejects_missing_command_parts_in_fan_in(tmp_path: Path):
    gate = _load_ci_workflow_command_guard_gate_module()
    payload = _sample_ci_workflow_plan()
    payload["fan_in"].pop("aggregation_command_parts")
    path = tmp_path / "ci_workflow_plan_bad_command_parts.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    try:
        gate.load_ci_workflow_plan(path)
        raised = False
    except ValueError:
        raised = True

    assert raised

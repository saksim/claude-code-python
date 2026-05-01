"""Contract tests for P2-21 Linux CI workflow governance gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_governance_gate_module():
    script_path = Path("scripts") / "run_p2_linux_ci_workflow_governance_gate.py"
    spec = importlib.util.spec_from_file_location("p2_linux_ci_workflow_governance_gate", script_path)
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


def _render_artifacts(
    gate,
    *,
    plan_path: Path,
    workflow_path: Path,
    metadata_path: Path,
    workflow_name: str = "Linux Unified Gate",
    python_version: str = "3.11",
    artifact_prefix: str = "linux-unified-summary",
) -> None:
    yaml_gate = gate._load_module(
        script_name="run_p2_linux_ci_workflow_yaml_gate.py",
        module_name="p2_linux_ci_workflow_yaml_gate_for_test",
    )
    plan = yaml_gate.load_ci_workflow_plan(plan_path)
    workflow_yaml = yaml_gate.build_ci_workflow_yaml(
        plan,
        workflow_name=workflow_name,
        python_version=python_version,
        artifact_prefix=artifact_prefix,
    )
    metadata = yaml_gate.build_render_metadata(
        plan,
        source_plan_path=plan_path.resolve(),
        workflow_output_path=workflow_path,
        artifact_prefix=artifact_prefix,
    )
    metadata["workflow_name"] = workflow_name

    workflow_path.parent.mkdir(parents=True, exist_ok=True)
    workflow_path.write_text(workflow_yaml, encoding="utf-8")
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def test_build_governance_report_passes_on_aligned_payload(tmp_path: Path):
    gate = _load_ci_workflow_governance_gate_module()
    plan_path = tmp_path / "ci_workflow_plan.json"
    workflow_path = tmp_path / ".github" / "workflows" / "linux_unified_gate.yml"
    metadata_path = tmp_path / ".claude" / "reports" / "linux_unified_gate" / "ci_workflow_render.json"

    plan_path.write_text(json.dumps(_sample_ci_workflow_plan(), indent=2), encoding="utf-8")
    _render_artifacts(gate, plan_path=plan_path, workflow_path=workflow_path, metadata_path=metadata_path)

    report = gate.build_governance_report(
        ci_workflow_plan_path=plan_path,
        workflow_path=workflow_path,
        metadata_path=metadata_path,
        workflow_name="Linux Unified Gate",
        python_version="3.11",
        artifact_prefix="linux-unified-summary",
        strict_generated_at=False,
    )

    assert report["overall_status"] == "passed"
    assert report["failed_checks"] == []
    assert report["command_guard"]["overall_status"] == "passed"
    assert report["lineage"]["source_match"] is True
    assert report["lineage"]["workflow_output_match"] is True


def test_build_governance_report_fails_on_workflow_drift(tmp_path: Path):
    gate = _load_ci_workflow_governance_gate_module()
    plan_path = tmp_path / "ci_workflow_plan.json"
    workflow_path = tmp_path / ".github" / "workflows" / "linux_unified_gate.yml"
    metadata_path = tmp_path / ".claude" / "reports" / "linux_unified_gate" / "ci_workflow_render.json"

    plan_path.write_text(json.dumps(_sample_ci_workflow_plan(), indent=2), encoding="utf-8")
    _render_artifacts(gate, plan_path=plan_path, workflow_path=workflow_path, metadata_path=metadata_path)
    workflow_path.write_text(workflow_path.read_text(encoding="utf-8").replace("workflow_dispatch", "workflow_call"), encoding="utf-8")

    report = gate.build_governance_report(
        ci_workflow_plan_path=plan_path,
        workflow_path=workflow_path,
        metadata_path=metadata_path,
        workflow_name="Linux Unified Gate",
        python_version="3.11",
        artifact_prefix="linux-unified-summary",
        strict_generated_at=False,
    )

    assert report["overall_status"] == "failed"
    assert "workflow_sync_drift" in report["failed_checks"]
    assert report["workflow_sync"]["workflow_drift"] is True


def test_build_governance_report_fails_on_command_guard_issues(tmp_path: Path):
    gate = _load_ci_workflow_governance_gate_module()
    plan_path = tmp_path / "ci_workflow_plan.json"
    workflow_path = tmp_path / ".github" / "workflows" / "linux_unified_gate.yml"
    metadata_path = tmp_path / ".claude" / "reports" / "linux_unified_gate" / "ci_workflow_render.json"

    payload = _sample_ci_workflow_plan()
    payload["fan_out_matrix"]["include"][0]["command"] = (
        "python scripts/run_p2_linux_unified_execution_gate.py --report-dir "
        ".claude/reports/linux_unified_gate/shards/shard-1 --shard-total 2 "
        "--shard-index 1 --continue-on-failure --dry-run"
    )
    plan_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _render_artifacts(gate, plan_path=plan_path, workflow_path=workflow_path, metadata_path=metadata_path)

    report = gate.build_governance_report(
        ci_workflow_plan_path=plan_path,
        workflow_path=workflow_path,
        metadata_path=metadata_path,
        workflow_name="Linux Unified Gate",
        python_version="3.11",
        artifact_prefix="linux-unified-summary",
        strict_generated_at=False,
    )

    assert report["overall_status"] == "failed"
    assert "command_guard_failed" in report["failed_checks"]
    assert report["command_guard"]["issue_count"] > 0


def test_build_governance_report_fails_on_metadata_lineage_mismatch(tmp_path: Path):
    gate = _load_ci_workflow_governance_gate_module()
    plan_path = tmp_path / "ci_workflow_plan.json"
    workflow_path = tmp_path / ".github" / "workflows" / "linux_unified_gate.yml"
    metadata_path = tmp_path / ".claude" / "reports" / "linux_unified_gate" / "ci_workflow_render.json"

    plan_path.write_text(json.dumps(_sample_ci_workflow_plan(), indent=2), encoding="utf-8")
    _render_artifacts(gate, plan_path=plan_path, workflow_path=workflow_path, metadata_path=metadata_path)

    metadata_payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata_payload["source_ci_workflow_plan"] = "/tmp/another-plan.json"
    metadata_path.write_text(json.dumps(metadata_payload, indent=2), encoding="utf-8")

    report = gate.build_governance_report(
        ci_workflow_plan_path=plan_path,
        workflow_path=workflow_path,
        metadata_path=metadata_path,
        workflow_name="Linux Unified Gate",
        python_version="3.11",
        artifact_prefix="linux-unified-summary",
        strict_generated_at=False,
    )

    assert report["overall_status"] == "failed"
    assert "lineage_mismatch" in report["failed_checks"]
    issue_codes = [item["code"] for item in report["lineage"]["issues"]]
    assert "source_ci_workflow_plan_mismatch" in issue_codes

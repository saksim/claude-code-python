"""Contract tests for P2-19 Linux CI workflow sync gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_sync_gate_module():
    script_path = Path("scripts") / "run_p2_linux_ci_workflow_sync_gate.py"
    spec = importlib.util.spec_from_file_location("p2_linux_ci_workflow_sync_gate", script_path)
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
                    "command": "python scripts/run_p2_linux_unified_execution_gate.py --shard-total 2 --shard-index 1",
                },
                {
                    "job_id": "linux-shard-2",
                    "shard_index": 2,
                    "shard_total": 2,
                    "total_tests": 2,
                    "report_dir": ".claude/reports/linux_unified_gate/shards/shard-2",
                    "summary_path": ".claude/reports/linux_unified_gate/shards/shard-2/summary.json",
                    "command": "python scripts/run_p2_linux_unified_execution_gate.py --shard-total 2 --shard-index 2",
                },
            ]
        },
        "fan_in": {
            "summary_paths": [
                ".claude/reports/linux_unified_gate/shards/shard-1/summary.json",
                ".claude/reports/linux_unified_gate/shards/shard-2/summary.json",
            ],
            "merged_summary_path": ".claude/reports/linux_unified_gate/merged_summary.json",
            "aggregation_command": "python scripts/run_p2_linux_shard_aggregation_gate.py --output .claude/reports/linux_unified_gate/merged_summary.json --summary .claude/reports/linux_unified_gate/shards/shard-1/summary.json --summary .claude/reports/linux_unified_gate/shards/shard-2/summary.json",
            "publish_command": "python scripts/run_p2_linux_report_publish_gate.py --merged-summary .claude/reports/linux_unified_gate/merged_summary.json --output-json .claude/reports/linux_unified_gate/final_report.json --output-markdown .claude/reports/linux_unified_gate/final_report.md",
            "final_report_json": ".claude/reports/linux_unified_gate/final_report.json",
            "final_report_markdown": ".claude/reports/linux_unified_gate/final_report.md",
        },
    }


def _write_plan(path: Path) -> None:
    path.write_text(json.dumps(_sample_ci_workflow_plan(), indent=2), encoding="utf-8")


def test_check_render_drift_detects_missing_artifacts(tmp_path: Path):
    gate = _load_ci_workflow_sync_gate_module()
    plan_path = tmp_path / "ci_workflow_plan.json"
    _write_plan(plan_path)

    expected_yaml, expected_metadata = gate.build_expected_artifacts(
        plan_path=plan_path,
        workflow_path=tmp_path / ".github" / "workflows" / "linux_unified_gate.yml",
        workflow_name="Linux Unified Gate",
        python_version="3.11",
        artifact_prefix="linux-unified-summary",
    )
    drift = gate.check_render_drift(
        expected_workflow_yaml=expected_yaml,
        expected_metadata=expected_metadata,
        workflow_path=tmp_path / ".github" / "workflows" / "linux_unified_gate.yml",
        metadata_path=tmp_path / ".claude" / "reports" / "linux_unified_gate" / "ci_workflow_render.json",
        strict_generated_at=False,
    )

    assert drift["workflow_missing"] is True
    assert drift["metadata_missing"] is True
    assert drift["workflow_drift"] is True
    assert drift["metadata_drift"] is True


def test_check_render_drift_detects_workflow_content_drift(tmp_path: Path):
    gate = _load_ci_workflow_sync_gate_module()
    plan_path = tmp_path / "ci_workflow_plan.json"
    _write_plan(plan_path)
    workflow_path = tmp_path / ".github" / "workflows" / "linux_unified_gate.yml"
    metadata_path = tmp_path / ".claude" / "reports" / "linux_unified_gate" / "ci_workflow_render.json"

    expected_yaml, expected_metadata = gate.build_expected_artifacts(
        plan_path=plan_path,
        workflow_path=workflow_path,
        workflow_name="Linux Unified Gate",
        python_version="3.11",
        artifact_prefix="linux-unified-summary",
    )

    workflow_path.parent.mkdir(parents=True, exist_ok=True)
    workflow_path.write_text(expected_yaml.replace("workflow_dispatch", "workflow_call"), encoding="utf-8")
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(expected_metadata, indent=2), encoding="utf-8")

    drift = gate.check_render_drift(
        expected_workflow_yaml=expected_yaml,
        expected_metadata=expected_metadata,
        workflow_path=workflow_path,
        metadata_path=metadata_path,
        strict_generated_at=False,
    )

    assert drift["workflow_drift"] is True
    assert "workflow_call" in drift["workflow_diff"]
    assert drift["metadata_drift"] is False


def test_check_render_drift_ignores_generated_at_by_default(tmp_path: Path):
    gate = _load_ci_workflow_sync_gate_module()
    plan_path = tmp_path / "ci_workflow_plan.json"
    _write_plan(plan_path)
    workflow_path = tmp_path / ".github" / "workflows" / "linux_unified_gate.yml"
    metadata_path = tmp_path / ".claude" / "reports" / "linux_unified_gate" / "ci_workflow_render.json"

    expected_yaml, expected_metadata = gate.build_expected_artifacts(
        plan_path=plan_path,
        workflow_path=workflow_path,
        workflow_name="Linux Unified Gate",
        python_version="3.11",
        artifact_prefix="linux-unified-summary",
    )

    workflow_path.parent.mkdir(parents=True, exist_ok=True)
    workflow_path.write_text(expected_yaml, encoding="utf-8")
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    actual_metadata = dict(expected_metadata)
    actual_metadata["generated_at"] = "2099-01-01T00:00:00+00:00"
    metadata_path.write_text(json.dumps(actual_metadata, indent=2), encoding="utf-8")

    drift = gate.check_render_drift(
        expected_workflow_yaml=expected_yaml,
        expected_metadata=expected_metadata,
        workflow_path=workflow_path,
        metadata_path=metadata_path,
        strict_generated_at=False,
    )
    assert drift["workflow_drift"] is False
    assert drift["metadata_drift"] is False

    strict_drift = gate.check_render_drift(
        expected_workflow_yaml=expected_yaml,
        expected_metadata=expected_metadata,
        workflow_path=workflow_path,
        metadata_path=metadata_path,
        strict_generated_at=True,
    )
    assert strict_drift["metadata_drift"] is True
    assert "generated_at" in strict_drift["metadata_diff"]

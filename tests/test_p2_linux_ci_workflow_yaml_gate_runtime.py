"""Contract tests for P2-18 Linux CI workflow YAML render gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_yaml_gate_module():
    script_path = Path("scripts") / "run_p2_linux_ci_workflow_yaml_gate.py"
    spec = importlib.util.spec_from_file_location("p2_linux_ci_workflow_yaml_gate", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_ci_workflow_plan() -> dict:
    return {
        "generated_at": "2026-04-30T00:00:00+00:00",
        "source_ci_matrix": "/tmp/ci_matrix.json",
        "shard_total": 3,
        "manifest_total_tests": 5,
        "selected_shards": 3,
        "skipped_empty_shards": False,
        "fan_out_matrix": {
            "include": [
                {
                    "job_id": "linux-shard-1",
                    "shard_index": 1,
                    "shard_total": 3,
                    "total_tests": 2,
                    "report_dir": ".claude/reports/linux_unified_gate/shards/shard-1",
                    "summary_path": ".claude/reports/linux_unified_gate/shards/shard-1/summary.json",
                    "command": "python scripts/run_p2_linux_unified_execution_gate.py --shard-total 3 --shard-index 1",
                },
                {
                    "job_id": "linux-shard-2",
                    "shard_index": 2,
                    "shard_total": 3,
                    "total_tests": 2,
                    "report_dir": ".claude/reports/linux_unified_gate/shards/shard-2",
                    "summary_path": ".claude/reports/linux_unified_gate/shards/shard-2/summary.json",
                    "command": "python scripts/run_p2_linux_unified_execution_gate.py --shard-total 3 --shard-index 2",
                },
                {
                    "job_id": "linux-shard-3",
                    "shard_index": 3,
                    "shard_total": 3,
                    "total_tests": 1,
                    "report_dir": ".claude/reports/linux_unified_gate/shards/shard-3",
                    "summary_path": ".claude/reports/linux_unified_gate/shards/shard-3/summary.json",
                    "command": "python scripts/run_p2_linux_unified_execution_gate.py --shard-total 3 --shard-index 3",
                },
            ]
        },
        "fan_in": {
            "summary_paths": [
                ".claude/reports/linux_unified_gate/shards/shard-1/summary.json",
                ".claude/reports/linux_unified_gate/shards/shard-2/summary.json",
                ".claude/reports/linux_unified_gate/shards/shard-3/summary.json",
            ],
            "merged_summary_path": ".claude/reports/linux_unified_gate/merged_summary.json",
            "aggregation_command": "python scripts/run_p2_linux_shard_aggregation_gate.py --output .claude/reports/linux_unified_gate/merged_summary.json --summary .claude/reports/linux_unified_gate/shards/shard-1/summary.json --summary .claude/reports/linux_unified_gate/shards/shard-2/summary.json --summary .claude/reports/linux_unified_gate/shards/shard-3/summary.json",
            "publish_command": "python scripts/run_p2_linux_report_publish_gate.py --merged-summary .claude/reports/linux_unified_gate/merged_summary.json --output-json .claude/reports/linux_unified_gate/final_report.json --output-markdown .claude/reports/linux_unified_gate/final_report.md",
            "final_report_json": ".claude/reports/linux_unified_gate/final_report.json",
            "final_report_markdown": ".claude/reports/linux_unified_gate/final_report.md",
        },
    }


def test_build_ci_workflow_yaml_contains_fan_out_and_fan_in_contract():
    gate = _load_ci_workflow_yaml_gate_module()
    workflow_yaml = gate.build_ci_workflow_yaml(
        _sample_ci_workflow_plan(),
        workflow_name="Linux Unified Gate",
        python_version="3.11",
        artifact_prefix="linux-unified-summary",
    )

    assert "name: \"Linux Unified Gate\"" in workflow_yaml
    assert "linux_fan_out:" in workflow_yaml
    assert "linux_fan_in:" in workflow_yaml
    assert "shard_index: 1" in workflow_yaml
    assert "command: \"python scripts/run_p2_linux_unified_execution_gate.py --shard-total 3 --shard-index 1\"" in workflow_yaml
    assert "run: ${{ matrix.command }}" in workflow_yaml
    assert "run: \"python scripts/run_p2_linux_shard_aggregation_gate.py --output .claude/reports/linux_unified_gate/merged_summary.json --summary .claude/reports/linux_unified_gate/shards/shard-1/summary.json --summary .claude/reports/linux_unified_gate/shards/shard-2/summary.json --summary .claude/reports/linux_unified_gate/shards/shard-3/summary.json\"" in workflow_yaml
    assert "run: \"python scripts/run_p2_linux_report_publish_gate.py --merged-summary .claude/reports/linux_unified_gate/merged_summary.json --output-json .claude/reports/linux_unified_gate/final_report.json --output-markdown .claude/reports/linux_unified_gate/final_report.md\"" in workflow_yaml
    assert "pattern: \"linux-unified-summary-*\"" in workflow_yaml
    assert "merge-multiple: true" in workflow_yaml


def test_build_render_metadata_contract():
    gate = _load_ci_workflow_yaml_gate_module()
    metadata = gate.build_render_metadata(
        _sample_ci_workflow_plan(),
        source_plan_path=Path("reports/ci_workflow_plan.json"),
        workflow_output_path=Path(".github/workflows/linux_unified_gate.yml"),
        artifact_prefix="linux-unified-summary",
    )

    assert metadata["source_ci_workflow_plan"].endswith("reports/ci_workflow_plan.json")
    assert metadata["workflow_output_path"].endswith(".github/workflows/linux_unified_gate.yml")
    assert metadata["selected_shards"] == 3
    assert metadata["manifest_total_tests"] == 5
    assert metadata["fan_in"]["merged_summary_path"].endswith("merged_summary.json")


def test_load_ci_workflow_plan_rejects_summary_order_mismatch(tmp_path: Path):
    gate = _load_ci_workflow_yaml_gate_module()
    payload = _sample_ci_workflow_plan()
    payload["fan_in"]["summary_paths"] = list(reversed(payload["fan_in"]["summary_paths"]))
    path = tmp_path / "ci_workflow_plan_bad_summary_order.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    try:
        gate.load_ci_workflow_plan(path)
        raised = False
    except ValueError:
        raised = True

    assert raised


def test_load_ci_workflow_plan_rejects_selected_shards_mismatch(tmp_path: Path):
    gate = _load_ci_workflow_yaml_gate_module()
    payload = _sample_ci_workflow_plan()
    payload["selected_shards"] = 2
    path = tmp_path / "ci_workflow_plan_bad_selected.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    try:
        gate.load_ci_workflow_plan(path)
        raised = False
    except ValueError:
        raised = True

    assert raised

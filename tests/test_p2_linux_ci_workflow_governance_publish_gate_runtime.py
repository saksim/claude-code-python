"""Contract tests for P2-22 Linux CI workflow governance publish gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_governance_publish_gate_module():
    script_path = Path("scripts") / "run_p2_linux_ci_workflow_governance_publish_gate.py"
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_governance_publish_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_governance_report() -> dict:
    return {
        "generated_at": "2026-04-30T00:00:00+00:00",
        "source_ci_workflow_plan": "/tmp/ci_workflow_plan.json",
        "workflow_path": "/tmp/.github/workflows/linux_unified_gate.yml",
        "metadata_path": "/tmp/.claude/reports/linux_unified_gate/ci_workflow_render.json",
        "strict_generated_at": False,
        "overall_status": "passed",
        "failed_checks": [],
        "workflow_sync": {
            "workflow_missing": False,
            "metadata_missing": False,
            "workflow_drift": False,
            "metadata_drift": False,
            "workflow_diff": "",
            "metadata_diff": "",
        },
        "command_guard": {
            "overall_status": "passed",
            "failed_commands": 0,
            "total_commands": 4,
            "issue_count": 0,
            "normalization_required": False,
            "issues": [],
        },
        "lineage": {
            "expected_source_ci_workflow_plan": "/tmp/ci_workflow_plan.json",
            "actual_source_ci_workflow_plan": "/tmp/ci_workflow_plan.json",
            "source_match": True,
            "expected_workflow_output_path": "/tmp/.github/workflows/linux_unified_gate.yml",
            "actual_workflow_output_path": "/tmp/.github/workflows/linux_unified_gate.yml",
            "workflow_output_match": True,
            "issues": [],
        },
    }


def test_build_governance_publish_payload_passes_on_aligned_report(tmp_path: Path):
    gate = _load_ci_workflow_governance_publish_gate_module()
    report_path = tmp_path / "ci_workflow_governance.json"
    report_path.write_text(json.dumps(_sample_governance_report(), indent=2), encoding="utf-8")

    report = gate.load_governance_report(report_path)
    payload = gate.build_governance_publish_payload(report, source_path=report_path.resolve())

    assert payload["overall_status"] == "passed"
    assert payload["should_execute_workflow"] is True
    assert payload["failed_checks"] == []
    assert payload["structural_issues"] == []


def test_build_governance_publish_payload_fails_on_reported_failed_checks(tmp_path: Path):
    gate = _load_ci_workflow_governance_publish_gate_module()
    payload = _sample_governance_report()
    payload["overall_status"] = "failed"
    payload["failed_checks"] = ["workflow_sync_drift", "command_guard_failed"]
    payload["workflow_sync"]["workflow_drift"] = True
    payload["command_guard"]["overall_status"] = "failed"
    payload["command_guard"]["failed_commands"] = 1
    payload["command_guard"]["issue_count"] = 2

    report_path = tmp_path / "ci_workflow_governance_failed.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_governance_report(report_path)
    publish_payload = gate.build_governance_publish_payload(report, source_path=report_path.resolve())

    assert publish_payload["overall_status"] == "failed"
    assert publish_payload["should_execute_workflow"] is False
    assert "workflow_sync_drift" in publish_payload["failed_checks"]
    assert "command_guard_failed" in publish_payload["failed_checks"]


def test_build_governance_publish_payload_detects_failed_check_mismatch(tmp_path: Path):
    gate = _load_ci_workflow_governance_publish_gate_module()
    payload = _sample_governance_report()
    payload["overall_status"] = "passed"
    payload["failed_checks"] = []
    payload["workflow_sync"]["workflow_drift"] = True

    report_path = tmp_path / "ci_workflow_governance_bad_checks.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_governance_report(report_path)
    publish_payload = gate.build_governance_publish_payload(report, source_path=report_path.resolve())

    assert publish_payload["overall_status"] == "failed"
    assert "failed_checks_mismatch" in publish_payload["structural_issues"]


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_governance_publish_gate_module()
    payload = _sample_governance_report()
    report_path = tmp_path / "ci_workflow_governance.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_governance_report(report_path)
    publish_payload = gate.build_governance_publish_payload(report, source_path=report_path.resolve())
    outputs = gate.build_github_output_values(
        publish_payload,
        output_json=Path(".claude/reports/linux_unified_gate/ci_workflow_governance_publish.json"),
        output_markdown=Path(".claude/reports/linux_unified_gate/ci_workflow_governance_publish.md"),
    )

    assert outputs["governance_status"] == "passed"
    assert outputs["governance_should_execute_workflow"] == "true"
    assert outputs["governance_failed_checks"] == "[]"
    assert outputs["governance_report_json"].endswith("ci_workflow_governance_publish.json")
    assert outputs["governance_report_markdown"].endswith("ci_workflow_governance_publish.md")


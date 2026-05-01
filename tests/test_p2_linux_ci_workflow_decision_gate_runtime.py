"""Contract tests for P2-23 Linux CI workflow execution decision gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_decision_gate_module():
    script_path = Path("scripts") / "run_p2_linux_ci_workflow_decision_gate.py"
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_decision_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_governance_publish_payload() -> dict:
    return {
        "generated_at": "2026-04-30T00:00:00+00:00",
        "source_governance_report": "/tmp/ci_workflow_governance.json",
        "reported_status": "passed",
        "computed_status": "passed",
        "overall_status": "passed",
        "should_execute_workflow": True,
        "failed_checks": [],
        "failed_check_count": 0,
        "structural_issues": [],
    }


def test_build_execution_decision_payload_approves_when_all_contracts_aligned(tmp_path: Path):
    gate = _load_ci_workflow_decision_gate_module()
    payload = _sample_governance_publish_payload()
    report_path = tmp_path / "ci_workflow_governance_publish.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    workflow_plan_path = tmp_path / "ci_workflow_plan.json"
    workflow_plan_path.write_text("{}", encoding="utf-8")
    workflow_yaml_path = tmp_path / ".github" / "workflows" / "linux_unified_gate.yml"
    workflow_yaml_path.parent.mkdir(parents=True, exist_ok=True)
    workflow_yaml_path.write_text("name: Linux Unified Gate\n", encoding="utf-8")

    report = gate.load_governance_publish_report(report_path)
    decision_payload = gate.build_execution_decision_payload(
        report,
        source_path=report_path.resolve(),
        workflow_plan_path=workflow_plan_path,
        workflow_path=workflow_yaml_path,
        on_block_policy="fail",
    )

    assert decision_payload["decision"] == "execute"
    assert decision_payload["decision_status"] == "approved"
    assert decision_payload["should_execute_workflow"] is True
    assert decision_payload["exit_code"] == 0
    assert decision_payload["reason_codes"] == ["governance_passed"]


def test_build_execution_decision_payload_blocks_when_failed_checks_present(tmp_path: Path):
    gate = _load_ci_workflow_decision_gate_module()
    payload = _sample_governance_publish_payload()
    payload["overall_status"] = "failed"
    payload["should_execute_workflow"] = False
    payload["failed_checks"] = ["workflow_sync_drift", "command_guard_failed"]
    payload["failed_check_count"] = 2
    report_path = tmp_path / "ci_workflow_governance_publish_failed.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_governance_publish_report(report_path)
    decision_payload = gate.build_execution_decision_payload(
        report,
        source_path=report_path.resolve(),
        workflow_plan_path=tmp_path / "ci_workflow_plan.json",
        workflow_path=tmp_path / ".github" / "workflows" / "linux_unified_gate.yml",
        on_block_policy="fail",
    )

    assert decision_payload["decision"] == "blocked"
    assert decision_payload["should_execute_workflow"] is False
    assert decision_payload["exit_code"] == 1
    assert "workflow_sync_drift" in decision_payload["reason_codes"]
    assert "command_guard_failed" in decision_payload["reason_codes"]


def test_build_execution_decision_payload_returns_zero_when_blocked_with_skip_policy(tmp_path: Path):
    gate = _load_ci_workflow_decision_gate_module()
    payload = _sample_governance_publish_payload()
    payload["overall_status"] = "failed"
    payload["should_execute_workflow"] = False
    payload["failed_checks"] = ["lineage_mismatch"]
    payload["failed_check_count"] = 1
    report_path = tmp_path / "ci_workflow_governance_publish_skip.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_governance_publish_report(report_path)
    decision_payload = gate.build_execution_decision_payload(
        report,
        source_path=report_path.resolve(),
        workflow_plan_path=tmp_path / "ci_workflow_plan.json",
        workflow_path=tmp_path / ".github" / "workflows" / "linux_unified_gate.yml",
        on_block_policy="skip",
    )

    assert decision_payload["decision"] == "blocked"
    assert decision_payload["should_execute_workflow"] is False
    assert decision_payload["exit_code"] == 0
    assert decision_payload["on_block_policy"] == "skip"


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_decision_gate_module()
    payload = _sample_governance_publish_payload()
    report_path = tmp_path / "ci_workflow_governance_publish.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    workflow_plan_path = tmp_path / "ci_workflow_plan.json"
    workflow_plan_path.write_text("{}", encoding="utf-8")
    workflow_yaml_path = tmp_path / ".github" / "workflows" / "linux_unified_gate.yml"
    workflow_yaml_path.parent.mkdir(parents=True, exist_ok=True)
    workflow_yaml_path.write_text("name: Linux Unified Gate\n", encoding="utf-8")

    report = gate.load_governance_publish_report(report_path)
    decision_payload = gate.build_execution_decision_payload(
        report,
        source_path=report_path.resolve(),
        workflow_plan_path=workflow_plan_path,
        workflow_path=workflow_yaml_path,
        on_block_policy="fail",
    )
    outputs = gate.build_github_output_values(
        decision_payload,
        output_json=Path(".claude/reports/linux_unified_gate/ci_workflow_execution_decision.json"),
        output_markdown=Path(".claude/reports/linux_unified_gate/ci_workflow_execution_decision.md"),
    )

    assert outputs["workflow_execution_decision"] == "execute"
    assert outputs["workflow_execution_status"] == "approved"
    assert outputs["workflow_execution_should_execute"] == "true"
    assert outputs["workflow_execution_exit_code"] == "0"
    assert outputs["workflow_execution_report_json"].endswith("ci_workflow_execution_decision.json")
    assert outputs["workflow_execution_report_markdown"].endswith("ci_workflow_execution_decision.md")


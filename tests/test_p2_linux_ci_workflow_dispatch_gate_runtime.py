"""Contract tests for P2-24 Linux CI workflow dispatch gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_dispatch_gate_module():
    script_path = Path("scripts") / "run_p2_linux_ci_workflow_dispatch_gate.py"
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_dispatch_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_execution_decision_payload() -> dict:
    return {
        "generated_at": "2026-04-30T00:00:00+00:00",
        "source_governance_publish_report": "/tmp/ci_workflow_governance_publish.json",
        "workflow_plan_path": "/tmp/ci_workflow_plan.json",
        "workflow_path": "/tmp/.github/workflows/linux_unified_gate.yml",
        "governance_overall_status": "passed",
        "decision": "execute",
        "decision_status": "approved",
        "should_execute_workflow": True,
        "on_block_policy": "fail",
        "exit_code": 0,
        "failed_checks": [],
        "failed_check_count": 0,
        "structural_issues": [],
        "structural_issue_count": 0,
        "missing_artifacts": [],
        "reason_codes": ["governance_passed"],
        "primary_reason": "governance_passed",
    }


def test_build_dispatch_payload_ready_when_execute_decision(tmp_path: Path):
    gate = _load_ci_workflow_dispatch_gate_module()
    payload = _sample_execution_decision_payload()
    report_path = tmp_path / "ci_workflow_execution_decision.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_execution_decision(report_path)
    dispatch_payload = gate.build_dispatch_payload(
        report,
        source_path=report_path.resolve(),
        workflow_ref="main",
        gh_executable="gh",
    )

    assert dispatch_payload["dispatch_status"] == "ready"
    assert dispatch_payload["dispatch_mode"] == "workflow_dispatch"
    assert dispatch_payload["should_dispatch_workflow"] is True
    assert dispatch_payload["dispatch_command_parts"][:3] == ["gh", "workflow", "run"]
    assert "--ref" in dispatch_payload["dispatch_command_parts"]


def test_build_dispatch_payload_blocked_when_decision_blocked(tmp_path: Path):
    gate = _load_ci_workflow_dispatch_gate_module()
    payload = _sample_execution_decision_payload()
    payload["decision"] = "blocked"
    payload["decision_status"] = "blocked"
    payload["should_execute_workflow"] = False
    payload["on_block_policy"] = "skip"
    payload["exit_code"] = 0
    payload["failed_checks"] = ["workflow_sync_drift"]
    payload["failed_check_count"] = 1
    payload["reason_codes"] = ["workflow_sync_drift"]
    payload["primary_reason"] = "workflow_sync_drift"
    report_path = tmp_path / "ci_workflow_execution_decision_blocked.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_execution_decision(report_path)
    dispatch_payload = gate.build_dispatch_payload(
        report,
        source_path=report_path.resolve(),
        workflow_ref="main",
        gh_executable="gh",
    )

    assert dispatch_payload["dispatch_status"] == "blocked"
    assert dispatch_payload["dispatch_mode"] == "none"
    assert dispatch_payload["should_dispatch_workflow"] is False
    assert dispatch_payload["dispatch_command"] == ""
    assert dispatch_payload["dispatch_command_parts"] == []
    assert dispatch_payload["exit_code"] == 0


def test_load_execution_decision_rejects_contract_mismatch(tmp_path: Path):
    gate = _load_ci_workflow_dispatch_gate_module()
    payload = _sample_execution_decision_payload()
    payload["decision"] = "execute"
    payload["decision_status"] = "approved"
    payload["should_execute_workflow"] = False
    report_path = tmp_path / "ci_workflow_execution_decision_bad_contract.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    try:
        gate.load_execution_decision(report_path)
        raised = False
    except ValueError:
        raised = True

    assert raised


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_dispatch_gate_module()
    payload = _sample_execution_decision_payload()
    report_path = tmp_path / "ci_workflow_execution_decision.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_execution_decision(report_path)
    dispatch_payload = gate.build_dispatch_payload(
        report,
        source_path=report_path.resolve(),
        workflow_ref="main",
        gh_executable="gh",
    )
    outputs = gate.build_github_output_values(
        dispatch_payload,
        output_json=Path(".claude/reports/linux_unified_gate/ci_workflow_dispatch.json"),
        output_markdown=Path(".claude/reports/linux_unified_gate/ci_workflow_dispatch.md"),
    )

    assert outputs["workflow_dispatch_status"] == "ready"
    assert outputs["workflow_dispatch_mode"] == "workflow_dispatch"
    assert outputs["workflow_dispatch_should_dispatch"] == "true"
    assert outputs["workflow_dispatch_exit_code"] == "0"
    assert outputs["workflow_dispatch_command"].startswith("gh workflow run")
    assert outputs["workflow_dispatch_report_json"].endswith("ci_workflow_dispatch.json")
    assert outputs["workflow_dispatch_report_markdown"].endswith("ci_workflow_dispatch.md")


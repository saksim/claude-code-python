"""Contract tests for P2-25 Linux CI workflow dispatch execution gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_dispatch_execution_gate_module():
    script_path = Path("scripts") / "run_p2_linux_ci_workflow_dispatch_execution_gate.py"
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_dispatch_execution_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_dispatch_payload() -> dict:
    return {
        "generated_at": "2026-04-30T00:00:00+00:00",
        "source_execution_decision_report": "/tmp/ci_workflow_execution_decision.json",
        "source_governance_publish_report": "/tmp/ci_workflow_governance_publish.json",
        "workflow_path": ".github/workflows/linux_unified_gate.yml",
        "workflow_plan_path": ".claude/reports/linux_unified_gate/ci_workflow_plan.json",
        "workflow_ref": "main",
        "decision": "execute",
        "decision_status": "approved",
        "dispatch_status": "ready",
        "dispatch_mode": "workflow_dispatch",
        "should_dispatch_workflow": True,
        "exit_code": 0,
        "on_block_policy": "fail",
        "reason_codes": ["governance_passed"],
        "failed_checks": [],
        "structural_issues": [],
        "missing_artifacts": [],
        "dispatch_command": "gh workflow run .github/workflows/linux_unified_gate.yml --ref main",
        "dispatch_command_parts": [
            "gh",
            "workflow",
            "run",
            ".github/workflows/linux_unified_gate.yml",
            "--ref",
            "main",
        ],
    }


def test_build_dispatch_execution_payload_ready_dry_run(tmp_path: Path):
    gate = _load_ci_workflow_dispatch_execution_gate_module()
    payload = _sample_dispatch_payload()
    report_path = tmp_path / "ci_workflow_dispatch.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_dispatch_report(report_path)
    execution_payload = gate.build_dispatch_execution_payload(
        report,
        source_path=report_path.resolve(),
        project_root=tmp_path,
        dry_run=True,
        command_result=None,
    )

    assert execution_payload["execution_status"] == "ready_dry_run"
    assert execution_payload["execution_exit_code"] == 0
    assert execution_payload["dispatch_attempted"] is False
    assert execution_payload["should_dispatch_workflow"] is True


def test_build_dispatch_execution_payload_blocked_preserves_policy_exit(tmp_path: Path):
    gate = _load_ci_workflow_dispatch_execution_gate_module()
    payload = _sample_dispatch_payload()
    payload["decision"] = "blocked"
    payload["decision_status"] = "blocked"
    payload["dispatch_status"] = "blocked"
    payload["dispatch_mode"] = "none"
    payload["should_dispatch_workflow"] = False
    payload["on_block_policy"] = "skip"
    payload["exit_code"] = 0
    payload["reason_codes"] = ["workflow_sync_drift"]
    payload["failed_checks"] = ["workflow_sync_drift"]
    payload["dispatch_command"] = ""
    payload["dispatch_command_parts"] = []
    report_path = tmp_path / "ci_workflow_dispatch_blocked.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_dispatch_report(report_path)
    execution_payload = gate.build_dispatch_execution_payload(
        report,
        source_path=report_path.resolve(),
        project_root=tmp_path,
        dry_run=False,
        command_result=None,
    )

    assert execution_payload["execution_status"] == "blocked"
    assert execution_payload["execution_exit_code"] == 0
    assert execution_payload["dispatch_attempted"] is False
    assert execution_payload["should_dispatch_workflow"] is False
    assert execution_payload["reason_codes"] == ["workflow_sync_drift"]


def test_load_dispatch_report_rejects_command_contract_mismatch(tmp_path: Path):
    gate = _load_ci_workflow_dispatch_execution_gate_module()
    payload = _sample_dispatch_payload()
    payload["dispatch_command_parts"] = [
        "gh",
        "workflow",
        "run",
        ".github/workflows/linux_unified_gate.yml",
        "--ref",
        "dev",
    ]
    report_path = tmp_path / "ci_workflow_dispatch_bad_contract.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    try:
        gate.load_dispatch_report(report_path)
        raised = False
    except ValueError:
        raised = True

    assert raised


def test_build_dispatch_execution_payload_marks_failed_command(tmp_path: Path):
    gate = _load_ci_workflow_dispatch_execution_gate_module()
    payload = _sample_dispatch_payload()
    report_path = tmp_path / "ci_workflow_dispatch.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_dispatch_report(report_path)
    execution_payload = gate.build_dispatch_execution_payload(
        report,
        source_path=report_path.resolve(),
        project_root=tmp_path,
        dry_run=False,
        command_result={
            "attempted": True,
            "returncode": 1,
            "stdout_tail": "",
            "stderr_tail": "dispatch failed",
            "error_type": "",
            "error_message": "",
        },
    )

    assert execution_payload["execution_status"] == "dispatch_failed"
    assert execution_payload["execution_exit_code"] == 1
    assert execution_payload["dispatch_attempted"] is True
    assert "dispatch_command_failed" in execution_payload["reason_codes"]


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_dispatch_execution_gate_module()
    payload = _sample_dispatch_payload()
    report_path = tmp_path / "ci_workflow_dispatch.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_dispatch_report(report_path)
    execution_payload = gate.build_dispatch_execution_payload(
        report,
        source_path=report_path.resolve(),
        project_root=tmp_path,
        dry_run=True,
        command_result=None,
    )
    outputs = gate.build_github_output_values(
        execution_payload,
        output_json=Path(".claude/reports/linux_unified_gate/ci_workflow_dispatch_execution.json"),
        output_markdown=Path(".claude/reports/linux_unified_gate/ci_workflow_dispatch_execution.md"),
    )

    assert outputs["workflow_dispatch_execution_status"] == "ready_dry_run"
    assert outputs["workflow_dispatch_execution_should_dispatch"] == "true"
    assert outputs["workflow_dispatch_execution_attempted"] == "false"
    assert outputs["workflow_dispatch_execution_exit_code"] == "0"
    assert outputs["workflow_dispatch_execution_report_json"].endswith(
        "ci_workflow_dispatch_execution.json"
    )
    assert outputs["workflow_dispatch_execution_report_markdown"].endswith(
        "ci_workflow_dispatch_execution.md"
    )

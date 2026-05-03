"""Contract tests for P2-27 Linux CI workflow dispatch trace gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_dispatch_trace_gate_module():
    script_path = Path("scripts") / "run_p2_linux_ci_workflow_dispatch_trace_gate.py"
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_dispatch_trace_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_dispatch_execution_payload() -> dict:
    return {
        "generated_at": "2026-04-30T00:00:00+00:00",
        "source_dispatch_report": "/tmp/ci_workflow_dispatch.json",
        "project_root": "/tmp",
        "decision": "execute",
        "decision_status": "approved",
        "dispatch_status": "ready",
        "dispatch_mode": "workflow_dispatch",
        "should_dispatch_workflow": True,
        "dispatch_attempted": True,
        "dispatch_command": "gh workflow run .github/workflows/linux_unified_gate.yml --ref main",
        "dispatch_command_parts": [
            "gh",
            "workflow",
            "run",
            ".github/workflows/linux_unified_gate.yml",
            "--ref",
            "main",
        ],
        "dry_run": False,
        "execution_status": "dispatched",
        "execution_exit_code": 0,
        "command_returncode": 0,
        "command_stdout_tail": (
            "created workflow run: "
            "https://github.com/acme/demo/actions/runs/1234567890"
        ),
        "command_stderr_tail": "",
        "execution_error_type": "",
        "execution_error_message": "",
        "on_block_policy": "fail",
        "reason_codes": ["dispatch_command_succeeded"],
        "failed_checks": [],
        "structural_issues": [],
        "missing_artifacts": [],
        "workflow_path": ".github/workflows/linux_unified_gate.yml",
        "workflow_ref": "main",
        "workflow_plan_path": ".claude/reports/linux_unified_gate/ci_workflow_plan.json",
    }


def test_build_dispatch_trace_payload_extracts_run_reference(tmp_path: Path):
    gate = _load_ci_workflow_dispatch_trace_gate_module()
    payload = _sample_dispatch_execution_payload()
    report_path = tmp_path / "ci_workflow_dispatch_execution.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    dispatch_execution_report = gate.load_dispatch_execution_report(report_path)
    trace_payload = gate.build_dispatch_trace_payload(
        dispatch_execution_report,
        source_path=report_path.resolve(),
        gh_executable="gh",
        poll_now=False,
        dry_run=False,
        project_root=tmp_path,
        poll_timeout_seconds=300,
    )

    assert trace_payload["tracking_status"] == "run_tracking_ready"
    assert trace_payload["should_poll_workflow_run"] is True
    assert trace_payload["run_id"] == 1234567890
    assert trace_payload["repo_owner"] == "acme"
    assert trace_payload["repo_name"] == "demo"
    assert trace_payload["trace_exit_code"] == 0
    assert trace_payload["poll_attempted"] is False
    assert trace_payload["poll_command_parts"][:3] == ["gh", "run", "view"]


def test_build_dispatch_trace_payload_handles_missing_run_reference(tmp_path: Path):
    gate = _load_ci_workflow_dispatch_trace_gate_module()
    payload = _sample_dispatch_execution_payload()
    payload["command_stdout_tail"] = "dispatch succeeded without URL"
    report_path = tmp_path / "ci_workflow_dispatch_execution_no_run_url.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    dispatch_execution_report = gate.load_dispatch_execution_report(report_path)
    trace_payload = gate.build_dispatch_trace_payload(
        dispatch_execution_report,
        source_path=report_path.resolve(),
        gh_executable="gh",
        poll_now=False,
        dry_run=False,
        project_root=tmp_path,
        poll_timeout_seconds=300,
    )

    assert trace_payload["tracking_status"] == "run_tracking_missing"
    assert trace_payload["should_poll_workflow_run"] is False
    assert trace_payload["trace_exit_code"] == 1
    assert "dispatch_run_reference_missing" in trace_payload["reason_codes"]


def test_build_dispatch_trace_payload_blocked_passthrough(tmp_path: Path):
    gate = _load_ci_workflow_dispatch_trace_gate_module()
    payload = _sample_dispatch_execution_payload()
    payload["execution_status"] = "blocked"
    payload["execution_exit_code"] = 0
    payload["should_dispatch_workflow"] = False
    payload["dispatch_attempted"] = False
    payload["command_returncode"] = None
    payload["command_stdout_tail"] = ""
    payload["reason_codes"] = ["workflow_sync_drift"]
    payload["failed_checks"] = ["workflow_sync_drift"]
    report_path = tmp_path / "ci_workflow_dispatch_execution_blocked.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    dispatch_execution_report = gate.load_dispatch_execution_report(report_path)
    trace_payload = gate.build_dispatch_trace_payload(
        dispatch_execution_report,
        source_path=report_path.resolve(),
        gh_executable="gh",
        poll_now=True,
        dry_run=False,
        project_root=tmp_path,
        poll_timeout_seconds=300,
    )

    assert trace_payload["tracking_status"] == "blocked"
    assert trace_payload["should_poll_workflow_run"] is False
    assert trace_payload["run_id"] is None
    assert trace_payload["trace_exit_code"] == 0
    assert trace_payload["poll_attempted"] is False


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_dispatch_trace_gate_module()
    payload = _sample_dispatch_execution_payload()
    report_path = tmp_path / "ci_workflow_dispatch_execution.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    dispatch_execution_report = gate.load_dispatch_execution_report(report_path)
    trace_payload = gate.build_dispatch_trace_payload(
        dispatch_execution_report,
        source_path=report_path.resolve(),
        gh_executable="gh",
        poll_now=False,
        dry_run=False,
        project_root=tmp_path,
        poll_timeout_seconds=300,
    )
    outputs = gate.build_github_output_values(
        trace_payload,
        output_json=Path(".claude/reports/linux_unified_gate/ci_workflow_dispatch_trace.json"),
        output_markdown=Path(".claude/reports/linux_unified_gate/ci_workflow_dispatch_trace.md"),
    )

    assert outputs["workflow_dispatch_trace_status"] == "run_tracking_ready"
    assert outputs["workflow_dispatch_trace_should_poll"] == "true"
    assert outputs["workflow_dispatch_trace_run_id"] == "1234567890"
    assert outputs["workflow_dispatch_trace_run_url"].endswith("/actions/runs/1234567890")
    assert outputs["workflow_dispatch_trace_exit_code"] == "0"
    assert outputs["workflow_dispatch_trace_report_json"].endswith("ci_workflow_dispatch_trace.json")
    assert outputs["workflow_dispatch_trace_report_markdown"].endswith(
        "ci_workflow_dispatch_trace.md"
    )

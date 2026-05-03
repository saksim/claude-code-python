"""Contract tests for P2-71 Linux CI workflow Linux validation terminal dispatch trace gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_linux_validation_terminal_dispatch_trace_gate_module():
    script_path = (
        Path("scripts")
        / "run_p2_lv_td_trace_gate.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_linux_validation_terminal_dispatch_trace_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_linux_validation_terminal_dispatch_execution_payload() -> dict:
    return {
        "generated_at": "2026-05-02T00:00:00+00:00",
        "source_linux_validation_terminal_dispatch_report": "/tmp/ci_workflow_linux_validation_terminal_dispatch.json",
        "project_root": "/tmp",
        "linux_validation_terminal_dispatch_execution_status": "dispatched",
        "linux_validation_terminal_dispatch_execution_decision": "dispatch_linux_validation_terminal",
        "linux_validation_terminal_dispatch_execution_exit_code": 0,
        "linux_validation_terminal_dispatch_execution_requires_manual_action": False,
        "linux_validation_terminal_dispatch_execution_channel": "release",
        "linux_validation_terminal_should_dispatch": True,
        "linux_validation_terminal_dispatch_attempted": True,
        "linux_validation_terminal_command": "python scripts/run_p2_linux_unified_pipeline_gate.py --continue-on-failure",
        "linux_validation_terminal_command_parts": [
            "python",
            "scripts/run_p2_linux_unified_pipeline_gate.py",
            "--continue-on-failure",
        ],
        "linux_validation_terminal_dispatch_command_returncode": 0,
        "linux_validation_terminal_dispatch_command_stdout_tail": (
            "created workflow run: https://github.com/acme/demo/actions/runs/9988776655"
        ),
        "linux_validation_terminal_dispatch_command_stderr_tail": "",
        "linux_validation_terminal_dispatch_error_type": "",
        "linux_validation_terminal_dispatch_error_message": "",
        "release_run_id": 9988776655,
        "release_run_url": "https://github.com/acme/demo/actions/runs/9988776655",
        "follow_up_queue_url": "",
        "reason_codes": ["linux_validation_terminal_dispatch_execution_command_succeeded"],
        "structural_issues": [],
        "missing_artifacts": [],
    }


def test_build_linux_validation_terminal_dispatch_trace_payload_extracts_run_reference(
    tmp_path: Path,
):
    gate = _load_ci_workflow_linux_validation_terminal_dispatch_trace_gate_module()
    payload = _sample_linux_validation_terminal_dispatch_execution_payload()
    report_path = tmp_path / "ci_workflow_linux_validation_terminal_dispatch_execution.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    execution_report = gate.load_linux_validation_terminal_dispatch_execution_report(report_path)
    trace_payload = gate.build_linux_validation_terminal_dispatch_trace_payload(
        execution_report,
        source_path=report_path.resolve(),
        gh_executable="gh",
        poll_now=False,
        dry_run=False,
        project_root=tmp_path,
        poll_timeout_seconds=300,
    )

    assert trace_payload["linux_validation_terminal_dispatch_trace_status"] == "run_tracking_ready"
    assert trace_payload["linux_validation_terminal_should_poll_workflow_run"] is True
    assert trace_payload["linux_validation_terminal_run_id"] == 9988776655
    assert trace_payload["linux_validation_terminal_repo_owner"] == "acme"
    assert trace_payload["linux_validation_terminal_repo_name"] == "demo"
    assert trace_payload["linux_validation_terminal_dispatch_trace_exit_code"] == 0
    assert trace_payload["linux_validation_terminal_poll_attempted"] is False
    assert trace_payload["linux_validation_terminal_poll_command_parts"][:3] == [
        "gh",
        "run",
        "view",
    ]


def test_build_linux_validation_terminal_dispatch_trace_payload_handles_missing_run_reference(
    tmp_path: Path,
):
    gate = _load_ci_workflow_linux_validation_terminal_dispatch_trace_gate_module()
    payload = _sample_linux_validation_terminal_dispatch_execution_payload()
    payload["linux_validation_terminal_dispatch_command_stdout_tail"] = (
        "dispatch succeeded without URL"
    )
    report_path = (
        tmp_path / "ci_workflow_linux_validation_terminal_dispatch_execution_missing_url.json"
    )
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    execution_report = gate.load_linux_validation_terminal_dispatch_execution_report(report_path)
    trace_payload = gate.build_linux_validation_terminal_dispatch_trace_payload(
        execution_report,
        source_path=report_path.resolve(),
        gh_executable="gh",
        poll_now=False,
        dry_run=False,
        project_root=tmp_path,
        poll_timeout_seconds=300,
    )

    assert (
        trace_payload["linux_validation_terminal_dispatch_trace_status"]
        == "run_tracking_missing"
    )
    assert trace_payload["linux_validation_terminal_should_poll_workflow_run"] is False
    assert trace_payload["linux_validation_terminal_dispatch_trace_exit_code"] == 1
    assert (
        "linux_validation_terminal_dispatch_run_reference_missing"
        in trace_payload["reason_codes"]
    )


def test_build_linux_validation_terminal_dispatch_trace_payload_dispatch_failed_passthrough(
    tmp_path: Path,
):
    gate = _load_ci_workflow_linux_validation_terminal_dispatch_trace_gate_module()
    payload = _sample_linux_validation_terminal_dispatch_execution_payload()
    payload["linux_validation_terminal_dispatch_execution_status"] = "dispatch_failed"
    payload["linux_validation_terminal_dispatch_execution_exit_code"] = 1
    payload["linux_validation_terminal_dispatch_command_returncode"] = 1
    payload["linux_validation_terminal_dispatch_command_stdout_tail"] = ""
    payload["linux_validation_terminal_dispatch_command_stderr_tail"] = "dispatch failed"
    payload["reason_codes"] = ["linux_validation_terminal_dispatch_execution_command_failed"]
    report_path = tmp_path / "ci_workflow_linux_validation_terminal_dispatch_execution_failed.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    execution_report = gate.load_linux_validation_terminal_dispatch_execution_report(report_path)
    trace_payload = gate.build_linux_validation_terminal_dispatch_trace_payload(
        execution_report,
        source_path=report_path.resolve(),
        gh_executable="gh",
        poll_now=True,
        dry_run=False,
        project_root=tmp_path,
        poll_timeout_seconds=300,
    )

    assert trace_payload["linux_validation_terminal_dispatch_trace_status"] == "dispatch_failed"
    assert trace_payload["linux_validation_terminal_should_poll_workflow_run"] is False
    assert trace_payload["linux_validation_terminal_run_id"] is None
    assert trace_payload["linux_validation_terminal_dispatch_trace_exit_code"] == 1
    assert trace_payload["linux_validation_terminal_poll_attempted"] is False


def test_load_linux_validation_terminal_dispatch_execution_report_rejects_contract_mismatch(
    tmp_path: Path,
):
    gate = _load_ci_workflow_linux_validation_terminal_dispatch_trace_gate_module()
    payload = _sample_linux_validation_terminal_dispatch_execution_payload()
    payload["linux_validation_terminal_dispatch_execution_status"] = "blocked"
    payload["linux_validation_terminal_should_dispatch"] = True
    report_path = (
        tmp_path / "ci_workflow_linux_validation_terminal_dispatch_execution_mismatch.json"
    )
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    try:
        gate.load_linux_validation_terminal_dispatch_execution_report(report_path)
        raised = False
    except ValueError:
        raised = True

    assert raised


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_linux_validation_terminal_dispatch_trace_gate_module()
    payload = _sample_linux_validation_terminal_dispatch_execution_payload()
    report_path = tmp_path / "ci_workflow_linux_validation_terminal_dispatch_execution.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    execution_report = gate.load_linux_validation_terminal_dispatch_execution_report(report_path)
    trace_payload = gate.build_linux_validation_terminal_dispatch_trace_payload(
        execution_report,
        source_path=report_path.resolve(),
        gh_executable="gh",
        poll_now=False,
        dry_run=False,
        project_root=tmp_path,
        poll_timeout_seconds=300,
    )
    outputs = gate.build_github_output_values(
        trace_payload,
        output_json=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_trace.json"
        ),
        output_markdown=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_trace.md"
        ),
    )

    assert outputs["workflow_linux_validation_terminal_dispatch_trace_status"] == (
        "run_tracking_ready"
    )
    assert outputs["workflow_linux_validation_terminal_dispatch_trace_should_poll"] == "true"
    assert outputs["workflow_linux_validation_terminal_dispatch_trace_run_id"] == "9988776655"
    assert outputs["workflow_linux_validation_terminal_dispatch_trace_run_url"].endswith(
        "/actions/runs/9988776655"
    )
    assert outputs["workflow_linux_validation_terminal_dispatch_trace_exit_code"] == "0"
    assert outputs["workflow_linux_validation_terminal_dispatch_trace_report_json"].endswith(
        "ci_workflow_linux_validation_terminal_dispatch_trace.json"
    )
    assert outputs["workflow_linux_validation_terminal_dispatch_trace_report_markdown"].endswith(
        "ci_workflow_linux_validation_terminal_dispatch_trace.md"
    )


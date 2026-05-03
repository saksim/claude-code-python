"""Contract tests for P2-32 Linux CI workflow release trace gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_release_trace_gate_module():
    script_path = Path("scripts") / "run_p2_linux_ci_workflow_release_trace_gate.py"
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_release_trace_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_release_trigger_payload() -> dict:
    return {
        "generated_at": "2026-04-30T00:00:00+00:00",
        "source_release_handoff_report": "/tmp/ci_workflow_release_handoff.json",
        "project_root": "/tmp",
        "source_terminal_publish_report": "/tmp/ci_workflow_terminal_publish.json",
        "source_dispatch_completion_report": "/tmp/ci_workflow_dispatch_completion.json",
        "source_dispatch_trace_report": "/tmp/ci_workflow_dispatch_trace.json",
        "source_dispatch_execution_report": "/tmp/ci_workflow_dispatch_execution.json",
        "source_dispatch_report": "/tmp/ci_workflow_dispatch.json",
        "handoff_status": "ready_for_release",
        "handoff_action": "promote",
        "should_trigger_release": True,
        "release_exit_code": 0,
        "release_trigger_status": "triggered",
        "release_trigger_exit_code": 0,
        "release_trigger_attempted": True,
        "release_command": (
            "gh workflow run .github/workflows/release.yml --ref main "
            "--raw-field source_release_handoff_report=/tmp/ci_workflow_release_handoff.json"
        ),
        "release_command_parts": [
            "gh",
            "workflow",
            "run",
            ".github/workflows/release.yml",
            "--ref",
            "main",
            "--raw-field",
            "source_release_handoff_report=/tmp/ci_workflow_release_handoff.json",
        ],
        "release_workflow_path": ".github/workflows/release.yml",
        "release_workflow_ref": "main",
        "target_environment": "production",
        "release_channel": "stable",
        "publish_status": "passed",
        "completion_status": "run_completed_success",
        "run_id": 2233445566,
        "run_url": "https://github.com/acme/demo/actions/runs/2233445566",
        "dry_run": False,
        "command_returncode": 0,
        "command_stdout_tail": (
            "created workflow run: "
            "https://github.com/acme/demo/actions/runs/2233445566"
        ),
        "command_stderr_tail": "",
        "trigger_error_type": "",
        "trigger_error_message": "",
        "reason_codes": ["release_trigger_command_succeeded"],
        "failed_checks": [],
        "structural_issues": [],
        "missing_artifacts": [],
    }


def test_build_release_trace_payload_extracts_run_reference(tmp_path: Path):
    gate = _load_ci_workflow_release_trace_gate_module()
    payload = _sample_release_trigger_payload()
    report_path = tmp_path / "ci_workflow_release_trigger.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    release_trigger_report = gate.load_release_trigger_report(report_path)
    trace_payload = gate.build_release_trace_payload(
        release_trigger_report,
        source_path=report_path.resolve(),
        gh_executable="gh",
        poll_now=False,
        dry_run=False,
        project_root=tmp_path,
        poll_timeout_seconds=300,
    )

    assert trace_payload["release_tracking_status"] == "release_run_tracking_ready"
    assert trace_payload["should_poll_release_run"] is True
    assert trace_payload["release_run_id"] == 2233445566
    assert trace_payload["repo_owner"] == "acme"
    assert trace_payload["repo_name"] == "demo"
    assert trace_payload["release_trace_exit_code"] == 0
    assert trace_payload["release_poll_attempted"] is False
    assert trace_payload["release_poll_command_parts"][:3] == ["gh", "run", "view"]


def test_build_release_trace_payload_handles_missing_run_reference(tmp_path: Path):
    gate = _load_ci_workflow_release_trace_gate_module()
    payload = _sample_release_trigger_payload()
    payload["command_stdout_tail"] = "release dispatch succeeded without run URL"
    report_path = tmp_path / "ci_workflow_release_trigger_missing_run.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    release_trigger_report = gate.load_release_trigger_report(report_path)
    trace_payload = gate.build_release_trace_payload(
        release_trigger_report,
        source_path=report_path.resolve(),
        gh_executable="gh",
        poll_now=False,
        dry_run=False,
        project_root=tmp_path,
        poll_timeout_seconds=300,
    )

    assert trace_payload["release_tracking_status"] == "release_run_tracking_missing"
    assert trace_payload["should_poll_release_run"] is False
    assert trace_payload["release_trace_exit_code"] == 1
    assert "release_run_reference_missing" in trace_payload["reason_codes"]


def test_build_release_trace_payload_trigger_failed_passthrough(tmp_path: Path):
    gate = _load_ci_workflow_release_trace_gate_module()
    payload = _sample_release_trigger_payload()
    payload["release_trigger_status"] = "trigger_failed"
    payload["release_trigger_exit_code"] = 1
    payload["command_returncode"] = 1
    payload["command_stdout_tail"] = ""
    payload["command_stderr_tail"] = "release dispatch failed"
    payload["reason_codes"] = ["release_trigger_command_failed"]
    report_path = tmp_path / "ci_workflow_release_trigger_failed.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    release_trigger_report = gate.load_release_trigger_report(report_path)
    trace_payload = gate.build_release_trace_payload(
        release_trigger_report,
        source_path=report_path.resolve(),
        gh_executable="gh",
        poll_now=True,
        dry_run=False,
        project_root=tmp_path,
        poll_timeout_seconds=300,
    )

    assert trace_payload["release_tracking_status"] == "release_trigger_failed"
    assert trace_payload["should_poll_release_run"] is False
    assert trace_payload["release_run_id"] is None
    assert trace_payload["release_trace_exit_code"] == 1
    assert trace_payload["release_poll_attempted"] is False


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_release_trace_gate_module()
    payload = _sample_release_trigger_payload()
    report_path = tmp_path / "ci_workflow_release_trigger.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    release_trigger_report = gate.load_release_trigger_report(report_path)
    trace_payload = gate.build_release_trace_payload(
        release_trigger_report,
        source_path=report_path.resolve(),
        gh_executable="gh",
        poll_now=False,
        dry_run=False,
        project_root=tmp_path,
        poll_timeout_seconds=300,
    )
    outputs = gate.build_github_output_values(
        trace_payload,
        output_json=Path(".claude/reports/linux_unified_gate/ci_workflow_release_trace.json"),
        output_markdown=Path(".claude/reports/linux_unified_gate/ci_workflow_release_trace.md"),
    )

    assert outputs["workflow_release_trace_status"] == "release_run_tracking_ready"
    assert outputs["workflow_release_trace_should_poll"] == "true"
    assert outputs["workflow_release_trace_run_id"] == "2233445566"
    assert outputs["workflow_release_trace_run_url"].endswith("/actions/runs/2233445566")
    assert outputs["workflow_release_trace_exit_code"] == "0"
    assert outputs["workflow_release_trace_report_json"].endswith(
        "ci_workflow_release_trace.json"
    )
    assert outputs["workflow_release_trace_report_markdown"].endswith(
        "ci_workflow_release_trace.md"
    )

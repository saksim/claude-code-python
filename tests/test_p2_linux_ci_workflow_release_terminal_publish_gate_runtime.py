"""Contract tests for P2-34 Linux CI workflow release terminal publish gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_release_terminal_publish_gate_module():
    script_path = Path("scripts") / "run_p2_linux_ci_workflow_release_terminal_publish_gate.py"
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_release_terminal_publish_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_release_completion_payload() -> dict:
    return {
        "generated_at": "2026-04-30T00:00:00+00:00",
        "source_release_trace_report": "/tmp/ci_workflow_release_trace.json",
        "project_root": "/tmp",
        "source_release_trigger_report": "/tmp/ci_workflow_release_trigger.json",
        "source_release_handoff_report": "/tmp/ci_workflow_release_handoff.json",
        "source_terminal_publish_report": "/tmp/ci_workflow_terminal_publish.json",
        "source_dispatch_completion_report": "/tmp/ci_workflow_dispatch_completion.json",
        "source_dispatch_trace_report": "/tmp/ci_workflow_dispatch_trace.json",
        "source_dispatch_execution_report": "/tmp/ci_workflow_dispatch_execution.json",
        "source_dispatch_report": "/tmp/ci_workflow_dispatch.json",
        "release_trigger_status": "triggered",
        "release_tracking_status": "release_run_tracking_ready",
        "release_completion_status": "release_run_completed_success",
        "release_completion_exit_code": 0,
        "dry_run": False,
        "allow_in_progress": False,
        "should_poll_release_run": True,
        "release_run_id": 2233445566,
        "release_run_url": "https://github.com/acme/demo/actions/runs/2233445566",
        "repo_owner": "acme",
        "repo_name": "demo",
        "release_workflow_path": ".github/workflows/release.yml",
        "release_workflow_ref": "main",
        "release_poll_command": (
            "gh run view 2233445566 --json "
            "databaseId,status,conclusion,url,workflowName,createdAt,updatedAt --repo acme/demo"
        ),
        "release_poll_command_parts": [
            "gh",
            "run",
            "view",
            "2233445566",
            "--json",
            "databaseId,status,conclusion,url,workflowName,createdAt,updatedAt",
            "--repo",
            "acme/demo",
        ],
        "poll_interval_seconds": 20,
        "max_polls": 10,
        "poll_timeout_seconds": 300,
        "poll_iterations": 1,
        "poll_attempted": True,
        "poll_returncode": 0,
        "poll_status": "completed",
        "poll_conclusion": "success",
        "poll_url": "https://github.com/acme/demo/actions/runs/2233445566",
        "poll_error_type": "",
        "poll_error_message": "",
        "poll_stdout_tail": "",
        "poll_stderr_tail": "",
        "release_trace_reason_codes": ["release_trigger_command_succeeded"],
        "reason_codes": ["release_run_completed_success"],
        "failed_checks": [],
        "structural_issues": [],
        "missing_artifacts": [],
    }


def test_build_release_terminal_publish_payload_marks_passed_and_finalize(tmp_path: Path):
    gate = _load_ci_workflow_release_terminal_publish_gate_module()
    payload = _sample_release_completion_payload()
    report_path = tmp_path / "ci_workflow_release_completion.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_completion_report(report_path)
    publish_payload = gate.build_release_terminal_publish_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert publish_payload["release_publish_status"] == "passed"
    assert publish_payload["release_publish_exit_code"] == 0
    assert publish_payload["should_finalize_release"] is True
    assert publish_payload["reason_codes"] == ["release_completed_success"]


def test_build_release_terminal_publish_payload_timeout_with_allow_in_progress(tmp_path: Path):
    gate = _load_ci_workflow_release_terminal_publish_gate_module()
    payload = _sample_release_completion_payload()
    payload["release_tracking_status"] = "release_run_in_progress"
    payload["release_completion_status"] = "release_run_await_timeout"
    payload["release_completion_exit_code"] = 0
    payload["allow_in_progress"] = True
    payload["reason_codes"] = ["release_run_await_timeout"]

    report_path = tmp_path / "ci_workflow_release_completion_timeout.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_completion_report(report_path)
    publish_payload = gate.build_release_terminal_publish_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert publish_payload["release_publish_status"] == "in_progress"
    assert publish_payload["release_publish_exit_code"] == 0
    assert publish_payload["should_finalize_release"] is False
    assert "release_run_await_timeout" in publish_payload["reason_codes"]


def test_build_release_terminal_publish_payload_rejects_contract_mismatch(tmp_path: Path):
    gate = _load_ci_workflow_release_terminal_publish_gate_module()
    payload = _sample_release_completion_payload()
    payload["release_completion_status"] = "release_run_completed_success"
    payload["release_completion_exit_code"] = 1

    report_path = tmp_path / "ci_workflow_release_completion_mismatch.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_completion_report(report_path)
    publish_payload = gate.build_release_terminal_publish_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert publish_payload["release_publish_status"] == "contract_failed"
    assert publish_payload["release_publish_exit_code"] == 1
    assert publish_payload["should_finalize_release"] is False
    assert "release_completion_exit_code_mismatch_success" in publish_payload["structural_issues"]


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_release_terminal_publish_gate_module()
    payload = _sample_release_completion_payload()
    payload["release_completion_status"] = "release_run_completed_failure"
    payload["release_completion_exit_code"] = 1
    payload["reason_codes"] = ["release_run_completed_with_failure"]

    report_path = tmp_path / "ci_workflow_release_completion_failed.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_completion_report(report_path)
    publish_payload = gate.build_release_terminal_publish_payload(
        report,
        source_path=report_path.resolve(),
    )
    outputs = gate.build_github_output_values(
        publish_payload,
        output_json=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_terminal_publish.json"
        ),
        output_markdown=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_terminal_publish.md"
        ),
    )

    assert outputs["workflow_release_terminal_publish_status"] == "failed"
    assert outputs["workflow_release_terminal_publish_exit_code"] == "1"
    assert outputs["workflow_release_terminal_publish_should_finalize_release"] == "false"
    assert outputs["workflow_release_terminal_publish_completion_status"] == (
        "release_run_completed_failure"
    )
    assert outputs["workflow_release_terminal_publish_run_id"] == "2233445566"
    assert outputs["workflow_release_terminal_publish_run_url"].endswith("/actions/runs/2233445566")
    assert outputs["workflow_release_terminal_publish_report_json"].endswith(
        "ci_workflow_release_terminal_publish.json"
    )
    assert outputs["workflow_release_terminal_publish_report_markdown"].endswith(
        "ci_workflow_release_terminal_publish.md"
    )


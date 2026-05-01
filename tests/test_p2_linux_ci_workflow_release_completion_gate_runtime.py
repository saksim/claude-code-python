"""Contract tests for P2-33 Linux CI workflow release completion gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_release_completion_gate_module():
    script_path = Path("scripts") / "run_p2_linux_ci_workflow_release_completion_gate.py"
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_release_completion_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_release_trace_payload() -> dict:
    return {
        "generated_at": "2026-04-30T00:00:00+00:00",
        "source_release_trigger_report": "/tmp/ci_workflow_release_trigger.json",
        "project_root": "/tmp",
        "source_release_handoff_report": "/tmp/ci_workflow_release_handoff.json",
        "source_terminal_publish_report": "/tmp/ci_workflow_terminal_publish.json",
        "source_dispatch_completion_report": "/tmp/ci_workflow_dispatch_completion.json",
        "source_dispatch_trace_report": "/tmp/ci_workflow_dispatch_trace.json",
        "source_dispatch_execution_report": "/tmp/ci_workflow_dispatch_execution.json",
        "source_dispatch_report": "/tmp/ci_workflow_dispatch.json",
        "handoff_status": "ready_for_release",
        "release_trigger_status": "triggered",
        "release_trigger_exit_code": 0,
        "should_trigger_release": True,
        "release_trigger_attempted": True,
        "target_environment": "production",
        "release_channel": "stable",
        "release_workflow_path": ".github/workflows/release.yml",
        "release_workflow_ref": "main",
        "release_tracking_status": "release_run_tracking_ready",
        "release_trace_exit_code": 0,
        "poll_now": False,
        "dry_run": False,
        "should_poll_release_run": True,
        "release_run_id": 2233445566,
        "release_run_url": "https://github.com/acme/demo/actions/runs/2233445566",
        "repo_owner": "acme",
        "repo_name": "demo",
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
        "release_poll_attempted": False,
        "release_poll_returncode": None,
        "release_poll_status": "",
        "release_poll_conclusion": "",
        "release_poll_url": "https://github.com/acme/demo/actions/runs/2233445566",
        "release_poll_error_type": "",
        "release_poll_error_message": "",
        "release_poll_stdout_tail": "",
        "release_poll_stderr_tail": "",
        "release_trigger_reason_codes": ["release_trigger_command_succeeded"],
        "reason_codes": ["release_trigger_command_succeeded"],
        "failed_checks": [],
        "structural_issues": [],
        "missing_artifacts": [],
    }


def _success_poll_result() -> dict:
    return {
        "returncode": 0,
        "stdout_tail": (
            '{"status":"completed","conclusion":"success",'
            '"url":"https://github.com/acme/demo/actions/runs/2233445566"}'
        ),
        "stderr_tail": "",
        "payload": {
            "status": "completed",
            "conclusion": "success",
            "url": "https://github.com/acme/demo/actions/runs/2233445566",
        },
        "error_type": "",
        "error_message": "",
    }


def test_build_release_completion_payload_reaches_success(tmp_path: Path):
    gate = _load_ci_workflow_release_completion_gate_module()
    payload = _sample_release_trace_payload()
    report_path = tmp_path / "ci_workflow_release_trace.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_trace_report(report_path)
    completion_payload = gate.build_release_completion_payload(
        report,
        source_path=report_path.resolve(),
        project_root=tmp_path,
        poll_interval_seconds=1,
        max_polls=3,
        poll_timeout_seconds=30,
        dry_run=False,
        allow_in_progress=False,
        poll_executor=lambda command_parts, cwd, timeout_seconds: _success_poll_result(),
        sleep_fn=lambda seconds: None,
    )

    assert completion_payload["release_completion_status"] == "release_run_completed_success"
    assert completion_payload["release_completion_exit_code"] == 0
    assert completion_payload["poll_attempted"] is True
    assert completion_payload["poll_iterations"] == 1
    assert completion_payload["poll_status"] == "completed"
    assert completion_payload["poll_conclusion"] == "success"
    assert completion_payload["reason_codes"] == ["release_run_completed_success"]


def test_build_release_completion_payload_timeout_without_allow_in_progress(tmp_path: Path):
    gate = _load_ci_workflow_release_completion_gate_module()
    payload = _sample_release_trace_payload()
    report_path = tmp_path / "ci_workflow_release_trace.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_trace_report(report_path)

    def _in_progress_result(command_parts, cwd, timeout_seconds):
        return {
            "returncode": 0,
            "stdout_tail": '{"status":"in_progress","conclusion":null}',
            "stderr_tail": "",
            "payload": {"status": "in_progress", "conclusion": None},
            "error_type": "",
            "error_message": "",
        }

    completion_payload = gate.build_release_completion_payload(
        report,
        source_path=report_path.resolve(),
        project_root=tmp_path,
        poll_interval_seconds=1,
        max_polls=2,
        poll_timeout_seconds=30,
        dry_run=False,
        allow_in_progress=False,
        poll_executor=_in_progress_result,
        sleep_fn=lambda seconds: None,
    )

    assert completion_payload["release_completion_status"] == "release_run_await_timeout"
    assert completion_payload["release_completion_exit_code"] == 1
    assert completion_payload["poll_attempted"] is True
    assert completion_payload["poll_iterations"] == 2
    assert "release_run_await_timeout" in completion_payload["reason_codes"]


def test_load_release_trace_report_rejects_command_contract_mismatch(tmp_path: Path):
    gate = _load_ci_workflow_release_completion_gate_module()
    payload = _sample_release_trace_payload()
    payload["release_poll_command_parts"] = [
        "gh",
        "run",
        "view",
        "2233445566",
        "--json",
        "databaseId,status",
    ]
    report_path = tmp_path / "ci_workflow_release_trace_bad.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    try:
        gate.load_release_trace_report(report_path)
        raised = False
    except ValueError:
        raised = True

    assert raised


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_release_completion_gate_module()
    payload = _sample_release_trace_payload()
    payload["release_tracking_status"] = "release_run_completed_failure"
    payload["release_trace_exit_code"] = 1
    payload["should_poll_release_run"] = False
    payload["release_run_id"] = None
    payload["release_poll_command"] = ""
    payload["release_poll_command_parts"] = []
    payload["reason_codes"] = ["release_run_completed_with_failure"]
    report_path = tmp_path / "ci_workflow_release_trace_terminal.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_trace_report(report_path)
    completion_payload = gate.build_release_completion_payload(
        report,
        source_path=report_path.resolve(),
        project_root=tmp_path,
        poll_interval_seconds=1,
        max_polls=1,
        poll_timeout_seconds=30,
        dry_run=False,
        allow_in_progress=False,
        sleep_fn=lambda seconds: None,
    )
    outputs = gate.build_github_output_values(
        completion_payload,
        output_json=Path(".claude/reports/linux_unified_gate/ci_workflow_release_completion.json"),
        output_markdown=Path(".claude/reports/linux_unified_gate/ci_workflow_release_completion.md"),
    )

    assert outputs["workflow_release_completion_status"] == "release_run_completed_failure"
    assert outputs["workflow_release_completion_exit_code"] == "1"
    assert outputs["workflow_release_completion_should_poll"] == "false"
    assert outputs["workflow_release_completion_poll_attempted"] == "false"
    assert outputs["workflow_release_completion_run_id"] == ""
    assert outputs["workflow_release_completion_report_json"].endswith(
        "ci_workflow_release_completion.json"
    )
    assert outputs["workflow_release_completion_report_markdown"].endswith(
        "ci_workflow_release_completion.md"
    )


"""Contract tests for P2-28 Linux CI workflow dispatch completion gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_dispatch_completion_gate_module():
    script_path = Path("scripts") / "run_p2_linux_ci_workflow_dispatch_completion_gate.py"
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_dispatch_completion_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_dispatch_trace_payload() -> dict:
    return {
        "generated_at": "2026-04-30T00:00:00+00:00",
        "source_dispatch_execution_report": "/tmp/ci_workflow_dispatch_execution.json",
        "source_dispatch_report": "/tmp/ci_workflow_dispatch.json",
        "project_root": "/tmp",
        "execution_status": "dispatched",
        "tracking_status": "run_tracking_ready",
        "trace_exit_code": 0,
        "poll_now": False,
        "dry_run": False,
        "should_poll_workflow_run": True,
        "run_id": 1234567890,
        "run_url": "https://github.com/acme/demo/actions/runs/1234567890",
        "repo_owner": "acme",
        "repo_name": "demo",
        "workflow_path": ".github/workflows/linux_unified_gate.yml",
        "workflow_ref": "main",
        "poll_command": (
            "gh run view 1234567890 --json "
            "databaseId,status,conclusion,url,workflowName,createdAt,updatedAt --repo acme/demo"
        ),
        "poll_command_parts": [
            "gh",
            "run",
            "view",
            "1234567890",
            "--json",
            "databaseId,status,conclusion,url,workflowName,createdAt,updatedAt",
            "--repo",
            "acme/demo",
        ],
        "poll_attempted": False,
        "poll_returncode": None,
        "poll_status": "",
        "poll_conclusion": "",
        "poll_url": "https://github.com/acme/demo/actions/runs/1234567890",
        "poll_error_type": "",
        "poll_error_message": "",
        "poll_stdout_tail": "",
        "poll_stderr_tail": "",
        "dispatch_reason_codes": ["dispatch_command_succeeded"],
        "reason_codes": ["dispatch_command_succeeded"],
        "failed_checks": [],
        "structural_issues": [],
        "missing_artifacts": [],
    }


def _success_poll_result() -> dict:
    return {
        "returncode": 0,
        "stdout_tail": '{"status":"completed","conclusion":"success","url":"https://github.com/acme/demo/actions/runs/1234567890"}',
        "stderr_tail": "",
        "payload": {
            "status": "completed",
            "conclusion": "success",
            "url": "https://github.com/acme/demo/actions/runs/1234567890",
        },
        "error_type": "",
        "error_message": "",
    }


def test_build_dispatch_completion_payload_reaches_success(tmp_path: Path):
    gate = _load_ci_workflow_dispatch_completion_gate_module()
    payload = _sample_dispatch_trace_payload()
    report_path = tmp_path / "ci_workflow_dispatch_trace.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_dispatch_trace_report(report_path)
    completion_payload = gate.build_dispatch_completion_payload(
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

    assert completion_payload["completion_status"] == "run_completed_success"
    assert completion_payload["completion_exit_code"] == 0
    assert completion_payload["poll_attempted"] is True
    assert completion_payload["poll_iterations"] == 1
    assert completion_payload["poll_status"] == "completed"
    assert completion_payload["poll_conclusion"] == "success"
    assert completion_payload["reason_codes"] == ["run_completed_success"]


def test_build_dispatch_completion_payload_timeout_without_allow_in_progress(tmp_path: Path):
    gate = _load_ci_workflow_dispatch_completion_gate_module()
    payload = _sample_dispatch_trace_payload()
    report_path = tmp_path / "ci_workflow_dispatch_trace.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_dispatch_trace_report(report_path)

    def _in_progress_result(command_parts, cwd, timeout_seconds):
        return {
            "returncode": 0,
            "stdout_tail": '{"status":"in_progress","conclusion":null}',
            "stderr_tail": "",
            "payload": {"status": "in_progress", "conclusion": None},
            "error_type": "",
            "error_message": "",
        }

    completion_payload = gate.build_dispatch_completion_payload(
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

    assert completion_payload["completion_status"] == "run_await_timeout"
    assert completion_payload["completion_exit_code"] == 1
    assert completion_payload["poll_attempted"] is True
    assert completion_payload["poll_iterations"] == 2
    assert "run_await_timeout" in completion_payload["reason_codes"]


def test_load_dispatch_trace_report_rejects_command_contract_mismatch(tmp_path: Path):
    gate = _load_ci_workflow_dispatch_completion_gate_module()
    payload = _sample_dispatch_trace_payload()
    payload["poll_command_parts"] = [
        "gh",
        "run",
        "view",
        "1234567890",
        "--json",
        "databaseId,status",
    ]
    report_path = tmp_path / "ci_workflow_dispatch_trace_bad.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    try:
        gate.load_dispatch_trace_report(report_path)
        raised = False
    except ValueError:
        raised = True

    assert raised


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_dispatch_completion_gate_module()
    payload = _sample_dispatch_trace_payload()
    payload["tracking_status"] = "run_completed_failure"
    payload["trace_exit_code"] = 1
    payload["should_poll_workflow_run"] = False
    payload["run_id"] = None
    payload["poll_command"] = ""
    payload["poll_command_parts"] = []
    payload["reason_codes"] = ["run_completed_with_failure"]
    report_path = tmp_path / "ci_workflow_dispatch_trace_terminal.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_dispatch_trace_report(report_path)
    completion_payload = gate.build_dispatch_completion_payload(
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
        output_json=Path(".claude/reports/linux_unified_gate/ci_workflow_dispatch_completion.json"),
        output_markdown=Path(".claude/reports/linux_unified_gate/ci_workflow_dispatch_completion.md"),
    )

    assert outputs["workflow_dispatch_completion_status"] == "run_completed_failure"
    assert outputs["workflow_dispatch_completion_exit_code"] == "1"
    assert outputs["workflow_dispatch_completion_should_poll"] == "false"
    assert outputs["workflow_dispatch_completion_poll_attempted"] == "false"
    assert outputs["workflow_dispatch_completion_run_id"] == ""
    assert outputs["workflow_dispatch_completion_report_json"].endswith(
        "ci_workflow_dispatch_completion.json"
    )
    assert outputs["workflow_dispatch_completion_report_markdown"].endswith(
        "ci_workflow_dispatch_completion.md"
    )


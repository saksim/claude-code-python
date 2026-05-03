"""Contract tests for P2-73 Linux CI workflow Linux validation terminal dispatch terminal publish gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_linux_validation_terminal_dispatch_terminal_publish_gate_module():
    script_path = (
        Path("scripts")
        / "run_p2_lv_td_terminal_publish_gate.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_linux_validation_terminal_dispatch_terminal_publish_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_linux_validation_terminal_dispatch_completion_payload() -> dict:
    return {
        "generated_at": "2026-05-03T00:00:00+00:00",
        "source_linux_validation_terminal_dispatch_trace_report": "/tmp/ci_workflow_linux_validation_terminal_dispatch_trace.json",
        "project_root": "/tmp",
        "source_linux_validation_terminal_dispatch_execution_report": "/tmp/ci_workflow_linux_validation_terminal_dispatch_execution.json",
        "source_linux_validation_terminal_dispatch_report": "/tmp/ci_workflow_linux_validation_terminal_dispatch.json",
        "linux_validation_terminal_dispatch_execution_status": "dispatched",
        "linux_validation_terminal_dispatch_execution_decision": "dispatch_linux_validation_terminal",
        "linux_validation_terminal_dispatch_execution_exit_code": 0,
        "linux_validation_terminal_should_dispatch": True,
        "linux_validation_terminal_dispatch_attempted": True,
        "linux_validation_terminal_dispatch_trace_status": "run_completed_success",
        "linux_validation_terminal_dispatch_trace_exit_code": 0,
        "linux_validation_terminal_dispatch_completion_status": "run_completed_success",
        "linux_validation_terminal_dispatch_completion_exit_code": 0,
        "dry_run": False,
        "allow_in_progress": False,
        "should_poll_workflow_run": True,
        "linux_validation_terminal_run_id": 9988776655,
        "linux_validation_terminal_run_url": "https://github.com/acme/demo/actions/runs/9988776655",
        "linux_validation_terminal_repo_owner": "acme",
        "linux_validation_terminal_repo_name": "demo",
        "linux_validation_terminal_poll_command": "gh run view 9988776655 --json databaseId,status,conclusion,url --repo acme/demo",
        "linux_validation_terminal_poll_command_parts": [
            "gh",
            "run",
            "view",
            "9988776655",
            "--json",
            "databaseId,status,conclusion,url",
            "--repo",
            "acme/demo",
        ],
        "poll_interval_seconds": 20,
        "max_polls": 15,
        "poll_timeout_seconds": 600,
        "poll_iterations": 1,
        "poll_attempted": True,
        "poll_returncode": 0,
        "poll_status": "completed",
        "poll_conclusion": "success",
        "poll_url": "https://github.com/acme/demo/actions/runs/9988776655",
        "poll_error_type": "",
        "poll_error_message": "",
        "poll_stdout_tail": '{"status":"completed","conclusion":"success"}',
        "poll_stderr_tail": "",
        "release_run_id": 9988776655,
        "release_run_url": "https://github.com/acme/demo/actions/runs/9988776655",
        "follow_up_queue_url": "",
        "reason_codes": ["linux_validation_terminal_dispatch_run_completed_success"],
        "structural_issues": [],
        "missing_artifacts": [],
    }


def test_build_linux_validation_terminal_dispatch_terminal_publish_payload_terminal_published(
    tmp_path: Path,
):
    gate = (
        _load_ci_workflow_linux_validation_terminal_dispatch_terminal_publish_gate_module()
    )
    completion_payload = _sample_linux_validation_terminal_dispatch_completion_payload()

    completion_path = (
        tmp_path / "ci_workflow_linux_validation_terminal_dispatch_completion.json"
    )
    completion_path.write_text(json.dumps(completion_payload, indent=2), encoding="utf-8")

    completion_report = gate.load_linux_validation_terminal_dispatch_completion_report(
        completion_path
    )
    terminal_publish_payload = (
        gate.build_linux_validation_terminal_dispatch_terminal_publish_payload(
            completion_report,
            source_path=completion_path.resolve(),
        )
    )

    assert (
        terminal_publish_payload[
            "linux_validation_terminal_dispatch_terminal_publish_status"
        ]
        == "terminal_published"
    )
    assert (
        terminal_publish_payload[
            "linux_validation_terminal_dispatch_terminal_publish_decision"
        ]
        == "announce_linux_validation_terminal_dispatch_completed"
    )
    assert (
        terminal_publish_payload[
            "linux_validation_terminal_dispatch_terminal_publish_exit_code"
        ]
        == 0
    )
    assert (
        terminal_publish_payload[
            "linux_validation_terminal_dispatch_terminal_publish_should_notify"
        ]
        is True
    )
    assert (
        terminal_publish_payload[
            "linux_validation_terminal_dispatch_terminal_publish_ready_for_handoff"
        ]
        is True
    )
    assert (
        terminal_publish_payload[
            "linux_validation_terminal_dispatch_terminal_publish_requires_manual_action"
        ]
        is False
    )
    assert (
        terminal_publish_payload[
            "linux_validation_terminal_dispatch_terminal_publish_channel"
        ]
        == "release"
    )


def test_build_linux_validation_terminal_dispatch_terminal_publish_payload_terminal_in_progress(
    tmp_path: Path,
):
    gate = (
        _load_ci_workflow_linux_validation_terminal_dispatch_terminal_publish_gate_module()
    )
    completion_payload = _sample_linux_validation_terminal_dispatch_completion_payload()
    completion_payload["linux_validation_terminal_dispatch_completion_status"] = (
        "run_await_timeout"
    )
    completion_payload["linux_validation_terminal_dispatch_completion_exit_code"] = 0
    completion_payload["allow_in_progress"] = True
    completion_payload["linux_validation_terminal_dispatch_trace_status"] = "run_in_progress"
    completion_payload["reason_codes"] = [
        "linux_validation_terminal_dispatch_run_await_timeout"
    ]

    completion_path = (
        tmp_path / "ci_workflow_linux_validation_terminal_dispatch_completion_timeout.json"
    )
    completion_path.write_text(json.dumps(completion_payload, indent=2), encoding="utf-8")

    completion_report = gate.load_linux_validation_terminal_dispatch_completion_report(
        completion_path
    )
    terminal_publish_payload = (
        gate.build_linux_validation_terminal_dispatch_terminal_publish_payload(
            completion_report,
            source_path=completion_path.resolve(),
        )
    )

    assert (
        terminal_publish_payload[
            "linux_validation_terminal_dispatch_terminal_publish_status"
        ]
        == "terminal_in_progress"
    )
    assert (
        terminal_publish_payload[
            "linux_validation_terminal_dispatch_terminal_publish_decision"
        ]
        == "announce_linux_validation_terminal_dispatch_in_progress"
    )
    assert (
        terminal_publish_payload[
            "linux_validation_terminal_dispatch_terminal_publish_exit_code"
        ]
        == 0
    )
    assert (
        terminal_publish_payload[
            "linux_validation_terminal_dispatch_terminal_publish_ready_for_handoff"
        ]
        is False
    )
    assert (
        terminal_publish_payload[
            "linux_validation_terminal_dispatch_terminal_publish_requires_manual_action"
        ]
        is False
    )


def test_build_linux_validation_terminal_dispatch_terminal_publish_payload_contract_failed_on_mismatch(
    tmp_path: Path,
):
    gate = (
        _load_ci_workflow_linux_validation_terminal_dispatch_terminal_publish_gate_module()
    )
    completion_payload = _sample_linux_validation_terminal_dispatch_completion_payload()
    completion_payload["linux_validation_terminal_dispatch_completion_status"] = (
        "run_completed_success"
    )
    completion_payload["linux_validation_terminal_dispatch_completion_exit_code"] = 1

    completion_path = (
        tmp_path / "ci_workflow_linux_validation_terminal_dispatch_completion_mismatch.json"
    )
    completion_path.write_text(json.dumps(completion_payload, indent=2), encoding="utf-8")

    completion_report = gate.load_linux_validation_terminal_dispatch_completion_report(
        completion_path
    )
    terminal_publish_payload = (
        gate.build_linux_validation_terminal_dispatch_terminal_publish_payload(
            completion_report,
            source_path=completion_path.resolve(),
        )
    )

    assert (
        terminal_publish_payload[
            "linux_validation_terminal_dispatch_terminal_publish_status"
        ]
        == "terminal_contract_failed"
    )
    assert (
        terminal_publish_payload[
            "linux_validation_terminal_dispatch_terminal_publish_decision"
        ]
        == "abort_linux_validation_terminal_dispatch_terminal_publish"
    )
    assert (
        terminal_publish_payload[
            "linux_validation_terminal_dispatch_terminal_publish_exit_code"
        ]
        == 1
    )
    assert (
        "linux_validation_terminal_dispatch_completion_exit_code_mismatch_success"
        in terminal_publish_payload["structural_issues"]
    )


def test_build_github_output_values_contract(tmp_path: Path):
    gate = (
        _load_ci_workflow_linux_validation_terminal_dispatch_terminal_publish_gate_module()
    )
    completion_payload = _sample_linux_validation_terminal_dispatch_completion_payload()
    completion_payload["linux_validation_terminal_dispatch_execution_status"] = (
        "ready_with_follow_up_dry_run"
    )
    completion_payload["linux_validation_terminal_dispatch_execution_decision"] = (
        "dispatch_linux_validation_terminal_with_follow_up"
    )
    completion_payload["linux_validation_terminal_dispatch_execution_exit_code"] = 1
    completion_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"

    completion_path = (
        tmp_path / "ci_workflow_linux_validation_terminal_dispatch_completion_output.json"
    )
    completion_path.write_text(json.dumps(completion_payload, indent=2), encoding="utf-8")

    completion_report = gate.load_linux_validation_terminal_dispatch_completion_report(
        completion_path
    )
    terminal_publish_payload = (
        gate.build_linux_validation_terminal_dispatch_terminal_publish_payload(
            completion_report,
            source_path=completion_path.resolve(),
        )
    )
    outputs = gate.build_github_output_values(
        terminal_publish_payload,
        output_json=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_publish.json"
        ),
        output_markdown=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_publish.md"
        ),
    )

    assert (
        outputs["workflow_linux_validation_terminal_dispatch_terminal_publish_status"]
        == "terminal_published_with_follow_up"
    )
    assert (
        outputs["workflow_linux_validation_terminal_dispatch_terminal_publish_decision"]
        == "announce_linux_validation_terminal_dispatch_completed_with_follow_up"
    )
    assert (
        outputs["workflow_linux_validation_terminal_dispatch_terminal_publish_exit_code"]
        == "1"
    )
    assert (
        outputs[
            "workflow_linux_validation_terminal_dispatch_terminal_publish_should_notify"
        ]
        == "true"
    )
    assert (
        outputs[
            "workflow_linux_validation_terminal_dispatch_terminal_publish_ready_for_handoff"
        ]
        == "true"
    )
    assert (
        outputs[
            "workflow_linux_validation_terminal_dispatch_terminal_publish_requires_manual_action"
        ]
        == "false"
    )
    assert (
        outputs["workflow_linux_validation_terminal_dispatch_terminal_publish_channel"]
        == "follow_up"
    )
    assert outputs[
        "workflow_linux_validation_terminal_dispatch_terminal_publish_follow_up_queue_url"
    ].endswith("/issues/77")
    assert (
        outputs["workflow_linux_validation_terminal_dispatch_terminal_publish_run_id"]
        == "9988776655"
    )
    assert outputs[
        "workflow_linux_validation_terminal_dispatch_terminal_publish_run_url"
    ].endswith("/actions/runs/9988776655")
    assert outputs[
        "workflow_linux_validation_terminal_dispatch_terminal_publish_report_json"
    ].endswith("ci_workflow_linux_validation_terminal_dispatch_terminal_publish.json")
    assert outputs[
        "workflow_linux_validation_terminal_dispatch_terminal_publish_report_markdown"
    ].endswith("ci_workflow_linux_validation_terminal_dispatch_terminal_publish.md")

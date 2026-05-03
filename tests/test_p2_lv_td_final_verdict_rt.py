"""Contract tests for P2-74 Linux CI workflow Linux validation terminal dispatch final verdict gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_linux_validation_terminal_dispatch_final_verdict_gate_module():
    script_path = (
        Path("scripts")
        / "run_p2_lv_td_final_verdict_gate.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_linux_validation_terminal_dispatch_final_verdict_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_linux_validation_terminal_dispatch_terminal_publish_payload() -> dict:
    return {
        "generated_at": "2026-05-03T00:00:00+00:00",
        "source_linux_validation_terminal_dispatch_completion_report": "/tmp/ci_workflow_linux_validation_terminal_dispatch_completion.json",
        "source_linux_validation_terminal_dispatch_trace_report": "/tmp/ci_workflow_linux_validation_terminal_dispatch_trace.json",
        "source_linux_validation_terminal_dispatch_execution_report": "/tmp/ci_workflow_linux_validation_terminal_dispatch_execution.json",
        "source_linux_validation_terminal_dispatch_report": "/tmp/ci_workflow_linux_validation_terminal_dispatch.json",
        "linux_validation_terminal_dispatch_completion_status": "run_completed_success",
        "linux_validation_terminal_dispatch_completion_exit_code": 0,
        "linux_validation_terminal_dispatch_execution_status": "dispatched",
        "linux_validation_terminal_dispatch_execution_decision": "dispatch_linux_validation_terminal",
        "linux_validation_terminal_dispatch_execution_exit_code": 0,
        "linux_validation_terminal_should_dispatch": True,
        "linux_validation_terminal_dispatch_attempted": True,
        "linux_validation_terminal_dispatch_trace_status": "run_completed_success",
        "linux_validation_terminal_dispatch_trace_exit_code": 0,
        "should_poll_workflow_run": True,
        "allow_in_progress": False,
        "linux_validation_terminal_run_id": 9988776655,
        "linux_validation_terminal_run_url": "https://github.com/acme/demo/actions/runs/9988776655",
        "release_run_id": 9988776655,
        "release_run_url": "https://github.com/acme/demo/actions/runs/9988776655",
        "follow_up_queue_url": "",
        "linux_validation_terminal_dispatch_terminal_publish_status": "terminal_published",
        "linux_validation_terminal_dispatch_terminal_publish_decision": "announce_linux_validation_terminal_dispatch_completed",
        "linux_validation_terminal_dispatch_terminal_publish_exit_code": 0,
        "linux_validation_terminal_dispatch_terminal_publish_should_notify": True,
        "linux_validation_terminal_dispatch_terminal_publish_ready_for_handoff": True,
        "linux_validation_terminal_dispatch_terminal_publish_requires_manual_action": False,
        "linux_validation_terminal_dispatch_terminal_publish_channel": "release",
        "linux_validation_terminal_dispatch_terminal_publish_summary": (
            "linux_validation_terminal_dispatch_completion_status=run_completed_success "
            "linux_validation_terminal_dispatch_terminal_publish_status=terminal_published "
            "linux_validation_terminal_dispatch_terminal_publish_decision=announce_linux_validation_terminal_dispatch_completed"
        ),
        "reason_codes": ["linux_validation_terminal_dispatch_terminal_publish_completed"],
        "structural_issues": [],
        "missing_artifacts": [],
    }


def test_build_linux_validation_terminal_dispatch_final_verdict_payload_validated(
    tmp_path: Path,
):
    gate = _load_ci_workflow_linux_validation_terminal_dispatch_final_verdict_gate_module()
    terminal_publish_payload = (
        _sample_linux_validation_terminal_dispatch_terminal_publish_payload()
    )

    report_path = (
        tmp_path / "ci_workflow_linux_validation_terminal_dispatch_terminal_publish.json"
    )
    report_path.write_text(json.dumps(terminal_publish_payload, indent=2), encoding="utf-8")

    report = gate.load_linux_validation_terminal_dispatch_terminal_publish_report(
        report_path
    )
    final_payload = gate.build_linux_validation_terminal_dispatch_final_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert (
        final_payload["linux_validation_terminal_dispatch_final_verdict_status"]
        == "validated"
    )
    assert (
        final_payload["linux_validation_terminal_dispatch_final_verdict_decision"]
        == "accept_linux_validation_terminal_dispatch"
    )
    assert (
        final_payload["linux_validation_terminal_dispatch_final_verdict_exit_code"] == 0
    )
    assert final_payload["linux_validation_terminal_dispatch_final_should_accept"] is True
    assert (
        final_payload["linux_validation_terminal_dispatch_final_requires_follow_up"]
        is False
    )
    assert (
        final_payload["linux_validation_terminal_dispatch_final_should_page_owner"]
        is False
    )
    assert final_payload["linux_validation_terminal_dispatch_final_channel"] == "release"
    assert final_payload["reason_codes"] == [
        "linux_validation_terminal_dispatch_final_verdict_validated"
    ]


def test_build_linux_validation_terminal_dispatch_final_verdict_payload_validated_with_follow_up(
    tmp_path: Path,
):
    gate = _load_ci_workflow_linux_validation_terminal_dispatch_final_verdict_gate_module()
    terminal_publish_payload = (
        _sample_linux_validation_terminal_dispatch_terminal_publish_payload()
    )
    terminal_publish_payload["linux_validation_terminal_dispatch_completion_status"] = (
        "run_completed_success"
    )
    terminal_publish_payload["linux_validation_terminal_dispatch_completion_exit_code"] = 1
    terminal_publish_payload["linux_validation_terminal_dispatch_execution_status"] = (
        "ready_with_follow_up_dry_run"
    )
    terminal_publish_payload["linux_validation_terminal_dispatch_execution_decision"] = (
        "dispatch_linux_validation_terminal_with_follow_up"
    )
    terminal_publish_payload["linux_validation_terminal_dispatch_execution_exit_code"] = 1
    terminal_publish_payload["follow_up_queue_url"] = (
        "https://github.com/acme/demo/issues/77"
    )
    terminal_publish_payload[
        "linux_validation_terminal_dispatch_terminal_publish_status"
    ] = "terminal_published_with_follow_up"
    terminal_publish_payload[
        "linux_validation_terminal_dispatch_terminal_publish_decision"
    ] = "announce_linux_validation_terminal_dispatch_completed_with_follow_up"
    terminal_publish_payload[
        "linux_validation_terminal_dispatch_terminal_publish_exit_code"
    ] = 1
    terminal_publish_payload[
        "linux_validation_terminal_dispatch_terminal_publish_channel"
    ] = "follow_up"
    terminal_publish_payload["reason_codes"] = [
        "linux_validation_terminal_dispatch_terminal_publish_with_follow_up"
    ]

    report_path = (
        tmp_path / "ci_workflow_linux_validation_terminal_dispatch_terminal_publish_follow_up.json"
    )
    report_path.write_text(json.dumps(terminal_publish_payload, indent=2), encoding="utf-8")

    report = gate.load_linux_validation_terminal_dispatch_terminal_publish_report(
        report_path
    )
    final_payload = gate.build_linux_validation_terminal_dispatch_final_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert (
        final_payload["linux_validation_terminal_dispatch_final_verdict_status"]
        == "validated_with_follow_up"
    )
    assert (
        final_payload["linux_validation_terminal_dispatch_final_verdict_decision"]
        == "accept_linux_validation_terminal_dispatch_with_follow_up"
    )
    assert (
        final_payload["linux_validation_terminal_dispatch_final_verdict_exit_code"] == 1
    )
    assert final_payload["linux_validation_terminal_dispatch_final_should_accept"] is True
    assert (
        final_payload["linux_validation_terminal_dispatch_final_requires_follow_up"]
        is True
    )
    assert (
        final_payload["linux_validation_terminal_dispatch_final_should_page_owner"]
        is False
    )
    assert final_payload["linux_validation_terminal_dispatch_final_channel"] == "follow_up"
    assert (
        "linux_validation_terminal_dispatch_final_verdict_validated_with_follow_up"
        in final_payload["reason_codes"]
    )
    assert final_payload["follow_up_queue_url"].endswith("/issues/77")


def test_build_linux_validation_terminal_dispatch_final_verdict_payload_blocked(
    tmp_path: Path,
):
    gate = _load_ci_workflow_linux_validation_terminal_dispatch_final_verdict_gate_module()
    terminal_publish_payload = (
        _sample_linux_validation_terminal_dispatch_terminal_publish_payload()
    )
    terminal_publish_payload["linux_validation_terminal_dispatch_completion_status"] = "blocked"
    terminal_publish_payload["linux_validation_terminal_dispatch_completion_exit_code"] = 1
    terminal_publish_payload["linux_validation_terminal_should_dispatch"] = False
    terminal_publish_payload["linux_validation_terminal_dispatch_execution_status"] = "blocked"
    terminal_publish_payload[
        "linux_validation_terminal_dispatch_execution_decision"
    ] = "hold_linux_validation_terminal_blocker"
    terminal_publish_payload["linux_validation_terminal_dispatch_execution_exit_code"] = 1
    terminal_publish_payload["linux_validation_terminal_dispatch_attempted"] = False
    terminal_publish_payload["linux_validation_terminal_dispatch_trace_status"] = "blocked"
    terminal_publish_payload["linux_validation_terminal_dispatch_trace_exit_code"] = 1
    terminal_publish_payload[
        "linux_validation_terminal_dispatch_terminal_publish_status"
    ] = "terminal_blocked"
    terminal_publish_payload[
        "linux_validation_terminal_dispatch_terminal_publish_decision"
    ] = "announce_linux_validation_terminal_dispatch_blocker"
    terminal_publish_payload[
        "linux_validation_terminal_dispatch_terminal_publish_exit_code"
    ] = 1
    terminal_publish_payload[
        "linux_validation_terminal_dispatch_terminal_publish_ready_for_handoff"
    ] = False
    terminal_publish_payload[
        "linux_validation_terminal_dispatch_terminal_publish_requires_manual_action"
    ] = True
    terminal_publish_payload[
        "linux_validation_terminal_dispatch_terminal_publish_channel"
    ] = "blocker"
    terminal_publish_payload["reason_codes"] = [
        "linux_validation_terminal_dispatch_terminal_publish_blocked"
    ]

    report_path = (
        tmp_path / "ci_workflow_linux_validation_terminal_dispatch_terminal_publish_blocked.json"
    )
    report_path.write_text(json.dumps(terminal_publish_payload, indent=2), encoding="utf-8")

    report = gate.load_linux_validation_terminal_dispatch_terminal_publish_report(
        report_path
    )
    final_payload = gate.build_linux_validation_terminal_dispatch_final_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert (
        final_payload["linux_validation_terminal_dispatch_final_verdict_status"]
        == "blocked"
    )
    assert (
        final_payload["linux_validation_terminal_dispatch_final_verdict_decision"]
        == "escalate_linux_validation_terminal_dispatch_blocker"
    )
    assert (
        final_payload["linux_validation_terminal_dispatch_final_verdict_exit_code"] == 1
    )
    assert final_payload["linux_validation_terminal_dispatch_final_should_accept"] is False
    assert (
        final_payload["linux_validation_terminal_dispatch_final_requires_follow_up"]
        is True
    )
    assert (
        final_payload["linux_validation_terminal_dispatch_final_should_page_owner"]
        is True
    )
    assert final_payload["linux_validation_terminal_dispatch_final_channel"] == "blocker"
    assert (
        "linux_validation_terminal_dispatch_final_verdict_blocked"
        in final_payload["reason_codes"]
    )


def test_build_linux_validation_terminal_dispatch_final_verdict_payload_contract_failed_on_mismatch(
    tmp_path: Path,
):
    gate = _load_ci_workflow_linux_validation_terminal_dispatch_final_verdict_gate_module()
    terminal_publish_payload = (
        _sample_linux_validation_terminal_dispatch_terminal_publish_payload()
    )
    terminal_publish_payload[
        "linux_validation_terminal_dispatch_terminal_publish_status"
    ] = "terminal_published"
    terminal_publish_payload[
        "linux_validation_terminal_dispatch_terminal_publish_decision"
    ] = "announce_linux_validation_terminal_dispatch_completed_with_follow_up"
    terminal_publish_payload[
        "linux_validation_terminal_dispatch_terminal_publish_ready_for_handoff"
    ] = False
    terminal_publish_payload[
        "linux_validation_terminal_dispatch_terminal_publish_requires_manual_action"
    ] = True
    terminal_publish_payload[
        "linux_validation_terminal_dispatch_terminal_publish_channel"
    ] = "follow_up"

    report_path = (
        tmp_path / "ci_workflow_linux_validation_terminal_dispatch_terminal_publish_mismatch.json"
    )
    report_path.write_text(json.dumps(terminal_publish_payload, indent=2), encoding="utf-8")

    report = gate.load_linux_validation_terminal_dispatch_terminal_publish_report(
        report_path
    )
    final_payload = gate.build_linux_validation_terminal_dispatch_final_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert (
        final_payload["linux_validation_terminal_dispatch_final_verdict_status"]
        == "contract_failed"
    )
    assert (
        final_payload["linux_validation_terminal_dispatch_final_verdict_decision"]
        == "abort_linux_validation_terminal_dispatch_final_verdict"
    )
    assert (
        final_payload["linux_validation_terminal_dispatch_final_verdict_exit_code"] == 1
    )
    assert (
        "linux_validation_terminal_dispatch_terminal_publish_decision_mismatch"
        in final_payload["structural_issues"]
    )
    assert (
        "linux_validation_terminal_dispatch_terminal_publish_ready_for_handoff_mismatch"
        in final_payload["structural_issues"]
    )
    assert (
        "linux_validation_terminal_dispatch_terminal_publish_requires_manual_action_mismatch"
        in final_payload["structural_issues"]
    )
    assert (
        "linux_validation_terminal_dispatch_terminal_publish_channel_mismatch"
        in final_payload["structural_issues"]
    )


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_linux_validation_terminal_dispatch_final_verdict_gate_module()
    terminal_publish_payload = (
        _sample_linux_validation_terminal_dispatch_terminal_publish_payload()
    )
    terminal_publish_payload[
        "linux_validation_terminal_dispatch_terminal_publish_status"
    ] = "terminal_published_with_follow_up"
    terminal_publish_payload[
        "linux_validation_terminal_dispatch_terminal_publish_decision"
    ] = "announce_linux_validation_terminal_dispatch_completed_with_follow_up"
    terminal_publish_payload[
        "linux_validation_terminal_dispatch_terminal_publish_exit_code"
    ] = 1
    terminal_publish_payload[
        "linux_validation_terminal_dispatch_terminal_publish_channel"
    ] = "follow_up"
    terminal_publish_payload["follow_up_queue_url"] = (
        "https://github.com/acme/demo/issues/77"
    )
    terminal_publish_payload["reason_codes"] = [
        "linux_validation_terminal_dispatch_terminal_publish_with_follow_up"
    ]

    report_path = (
        tmp_path / "ci_workflow_linux_validation_terminal_dispatch_terminal_publish_output.json"
    )
    report_path.write_text(json.dumps(terminal_publish_payload, indent=2), encoding="utf-8")

    report = gate.load_linux_validation_terminal_dispatch_terminal_publish_report(
        report_path
    )
    final_payload = gate.build_linux_validation_terminal_dispatch_final_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )
    outputs = gate.build_github_output_values(
        final_payload,
        output_json=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_final_verdict.json"
        ),
        output_markdown=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_final_verdict.md"
        ),
    )

    assert (
        outputs["workflow_linux_validation_terminal_dispatch_final_verdict_status"]
        == "validated_with_follow_up"
    )
    assert (
        outputs["workflow_linux_validation_terminal_dispatch_final_verdict_decision"]
        == "accept_linux_validation_terminal_dispatch_with_follow_up"
    )
    assert (
        outputs["workflow_linux_validation_terminal_dispatch_final_verdict_exit_code"]
        == "1"
    )
    assert (
        outputs["workflow_linux_validation_terminal_dispatch_final_should_accept"]
        == "true"
    )
    assert (
        outputs[
            "workflow_linux_validation_terminal_dispatch_final_requires_follow_up"
        ]
        == "true"
    )
    assert (
        outputs["workflow_linux_validation_terminal_dispatch_final_should_page_owner"]
        == "false"
    )
    assert (
        outputs["workflow_linux_validation_terminal_dispatch_final_channel"]
        == "follow_up"
    )
    assert (
        outputs[
            "workflow_linux_validation_terminal_dispatch_final_terminal_publish_status"
        ]
        == "terminal_published_with_follow_up"
    )
    assert (
        outputs[
            "workflow_linux_validation_terminal_dispatch_final_terminal_publish_channel"
        ]
        == "follow_up"
    )
    assert outputs[
        "workflow_linux_validation_terminal_dispatch_final_follow_up_queue_url"
    ].endswith("/issues/77")
    assert outputs["workflow_linux_validation_terminal_dispatch_final_run_id"] == "9988776655"
    assert outputs["workflow_linux_validation_terminal_dispatch_final_run_url"].endswith(
        "/actions/runs/9988776655"
    )
    assert outputs[
        "workflow_linux_validation_terminal_dispatch_final_report_json"
    ].endswith("ci_workflow_linux_validation_terminal_dispatch_final_verdict.json")
    assert outputs[
        "workflow_linux_validation_terminal_dispatch_final_report_markdown"
    ].endswith("ci_workflow_linux_validation_terminal_dispatch_final_verdict.md")

"""Contract tests for P2-36 Linux CI workflow release closure gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_release_closure_gate_module():
    script_path = Path("scripts") / "run_p2_linux_ci_workflow_release_closure_gate.py"
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_release_closure_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_release_finalization_payload() -> dict:
    return {
        "generated_at": "2026-04-30T00:00:00+00:00",
        "source_release_terminal_publish_report": "/tmp/ci_workflow_release_terminal_publish.json",
        "source_release_completion_report": "/tmp/ci_workflow_release_completion.json",
        "source_release_trace_report": "/tmp/ci_workflow_release_trace.json",
        "source_release_trigger_report": "/tmp/ci_workflow_release_trigger.json",
        "source_release_handoff_report": "/tmp/ci_workflow_release_handoff.json",
        "source_terminal_publish_report": "/tmp/ci_workflow_terminal_publish.json",
        "source_dispatch_completion_report": "/tmp/ci_workflow_dispatch_completion.json",
        "source_dispatch_trace_report": "/tmp/ci_workflow_dispatch_trace.json",
        "source_dispatch_execution_report": "/tmp/ci_workflow_dispatch_execution.json",
        "source_dispatch_report": "/tmp/ci_workflow_dispatch.json",
        "release_trigger_status": "triggered",
        "release_tracking_status": "release_run_completed_success",
        "release_completion_status": "release_run_completed_success",
        "release_completion_exit_code": 0,
        "release_publish_status": "passed",
        "release_publish_exit_code": 0,
        "release_finalization_status": "finalized",
        "release_finalization_decision": "finalize",
        "release_finalization_exit_code": 0,
        "should_finalize_release": True,
        "on_hold_policy": "pass",
        "allow_in_progress": False,
        "should_poll_release_run": True,
        "release_run_id": 2233445566,
        "release_run_url": "https://github.com/acme/demo/actions/runs/2233445566",
        "reason_codes": ["release_finalized"],
        "failed_checks": [],
        "structural_issues": [],
        "missing_artifacts": [],
    }


def test_build_release_closure_payload_marks_closed(tmp_path: Path):
    gate = _load_ci_workflow_release_closure_gate_module()
    payload = _sample_release_finalization_payload()
    report_path = tmp_path / "ci_workflow_release_finalization.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_finalization_report(report_path)
    closure_payload = gate.build_release_closure_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert closure_payload["release_closure_status"] == "closed"
    assert closure_payload["release_closure_decision"] == "ship"
    assert closure_payload["should_close_release"] is True
    assert closure_payload["release_closure_exit_code"] == 0
    assert closure_payload["reason_codes"] == ["release_closed"]


def test_build_release_closure_payload_pending_hold_path(tmp_path: Path):
    gate = _load_ci_workflow_release_closure_gate_module()
    payload = _sample_release_finalization_payload()
    payload["release_tracking_status"] = "release_run_in_progress"
    payload["release_completion_status"] = "release_run_await_timeout"
    payload["release_publish_status"] = "in_progress"
    payload["release_publish_exit_code"] = 0
    payload["release_finalization_status"] = "awaiting_release"
    payload["release_finalization_decision"] = "hold"
    payload["release_finalization_exit_code"] = 1
    payload["should_finalize_release"] = False
    payload["on_hold_policy"] = "fail"
    payload["reason_codes"] = ["release_run_await_timeout", "on_hold_policy_fail"]

    report_path = tmp_path / "ci_workflow_release_finalization_hold.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_finalization_report(report_path)
    closure_payload = gate.build_release_closure_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert closure_payload["release_closure_status"] == "pending"
    assert closure_payload["release_closure_decision"] == "hold"
    assert closure_payload["should_close_release"] is False
    assert closure_payload["release_closure_exit_code"] == 1
    assert "on_hold_policy_fail" in closure_payload["reason_codes"]


def test_build_release_closure_payload_rejects_contract_mismatch(tmp_path: Path):
    gate = _load_ci_workflow_release_closure_gate_module()
    payload = _sample_release_finalization_payload()
    payload["release_finalization_status"] = "finalized"
    payload["release_finalization_decision"] = "hold"
    payload["release_finalization_exit_code"] = 0
    payload["should_finalize_release"] = True

    report_path = tmp_path / "ci_workflow_release_finalization_mismatch.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_finalization_report(report_path)
    closure_payload = gate.build_release_closure_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert closure_payload["release_closure_status"] == "contract_failed"
    assert closure_payload["release_closure_decision"] == "rollback"
    assert closure_payload["release_closure_exit_code"] == 1
    assert "release_finalization_decision_mismatch_finalized" in closure_payload[
        "structural_issues"
    ]


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_release_closure_gate_module()
    payload = _sample_release_finalization_payload()
    payload["release_publish_status"] = "failed"
    payload["release_publish_exit_code"] = 1
    payload["release_finalization_status"] = "failed"
    payload["release_finalization_decision"] = "abort"
    payload["release_finalization_exit_code"] = 1
    payload["should_finalize_release"] = False
    payload["reason_codes"] = ["release_run_completed_with_failure"]

    report_path = tmp_path / "ci_workflow_release_finalization_failed.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_finalization_report(report_path)
    closure_payload = gate.build_release_closure_payload(
        report,
        source_path=report_path.resolve(),
    )
    outputs = gate.build_github_output_values(
        closure_payload,
        output_json=Path(".claude/reports/linux_unified_gate/ci_workflow_release_closure.json"),
        output_markdown=Path(".claude/reports/linux_unified_gate/ci_workflow_release_closure.md"),
    )

    assert outputs["workflow_release_closure_status"] == "failed"
    assert outputs["workflow_release_closure_decision"] == "rollback"
    assert outputs["workflow_release_closure_should_close_release"] == "false"
    assert outputs["workflow_release_closure_should_notify"] == "true"
    assert outputs["workflow_release_closure_exit_code"] == "1"
    assert outputs["workflow_release_closure_finalization_status"] == "failed"
    assert outputs["workflow_release_closure_run_id"] == "2233445566"
    assert outputs["workflow_release_closure_run_url"].endswith("/actions/runs/2233445566")
    assert outputs["workflow_release_closure_report_json"].endswith(
        "ci_workflow_release_closure.json"
    )
    assert outputs["workflow_release_closure_report_markdown"].endswith(
        "ci_workflow_release_closure.md"
    )

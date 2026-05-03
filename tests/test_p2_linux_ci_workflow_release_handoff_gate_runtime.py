"""Contract tests for P2-30 Linux CI workflow release handoff gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_release_handoff_gate_module():
    script_path = Path("scripts") / "run_p2_linux_ci_workflow_release_handoff_gate.py"
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_release_handoff_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_terminal_publish_payload() -> dict:
    return {
        "generated_at": "2026-04-30T00:00:00+00:00",
        "source_dispatch_completion_report": "/tmp/ci_workflow_dispatch_completion.json",
        "source_dispatch_trace_report": "/tmp/ci_workflow_dispatch_trace.json",
        "source_dispatch_execution_report": "/tmp/ci_workflow_dispatch_execution.json",
        "source_dispatch_report": "/tmp/ci_workflow_dispatch.json",
        "completion_status": "run_completed_success",
        "completion_exit_code": 0,
        "publish_status": "passed",
        "publish_exit_code": 0,
        "should_promote": True,
        "publish_summary": (
            "completion_status=run_completed_success publish_status=passed "
            "should_promote=True"
        ),
        "execution_status": "dispatched",
        "tracking_status": "run_completed_success",
        "allow_in_progress": False,
        "should_poll_workflow_run": True,
        "run_id": 1234567890,
        "run_url": "https://github.com/acme/demo/actions/runs/1234567890",
        "reason_codes": ["workflow_completed_success"],
        "failed_checks": [],
        "structural_issues": [],
        "missing_artifacts": [],
    }


def test_build_release_handoff_payload_ready_for_release(tmp_path: Path):
    gate = _load_ci_workflow_release_handoff_gate_module()
    payload = _sample_terminal_publish_payload()
    report_path = tmp_path / "ci_workflow_terminal_publish.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_terminal_publish_report(report_path)
    handoff_payload = gate.build_release_handoff_payload(
        report,
        source_path=report_path.resolve(),
        target_environment="production",
        release_channel="stable",
    )

    assert handoff_payload["handoff_status"] == "ready_for_release"
    assert handoff_payload["handoff_action"] == "promote"
    assert handoff_payload["should_trigger_release"] is True
    assert handoff_payload["release_exit_code"] == 0
    assert handoff_payload["reason_codes"] == ["release_ready"]


def test_build_release_handoff_payload_awaiting_completion(tmp_path: Path):
    gate = _load_ci_workflow_release_handoff_gate_module()
    payload = _sample_terminal_publish_payload()
    payload["publish_status"] = "in_progress"
    payload["publish_exit_code"] = 0
    payload["should_promote"] = False
    payload["completion_status"] = "run_await_timeout"
    payload["reason_codes"] = ["run_await_timeout"]

    report_path = tmp_path / "ci_workflow_terminal_publish_in_progress.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_terminal_publish_report(report_path)
    handoff_payload = gate.build_release_handoff_payload(
        report,
        source_path=report_path.resolve(),
        target_environment="production",
        release_channel="stable",
    )

    assert handoff_payload["handoff_status"] == "awaiting_completion"
    assert handoff_payload["handoff_action"] == "hold"
    assert handoff_payload["should_trigger_release"] is False
    assert handoff_payload["release_exit_code"] == 0
    assert "run_await_timeout" in handoff_payload["reason_codes"]


def test_build_release_handoff_payload_rejects_contract_mismatch(tmp_path: Path):
    gate = _load_ci_workflow_release_handoff_gate_module()
    payload = _sample_terminal_publish_payload()
    payload["publish_status"] = "passed"
    payload["publish_exit_code"] = 0
    payload["should_promote"] = False

    report_path = tmp_path / "ci_workflow_terminal_publish_mismatch.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_terminal_publish_report(report_path)
    handoff_payload = gate.build_release_handoff_payload(
        report,
        source_path=report_path.resolve(),
        target_environment="production",
        release_channel="stable",
    )

    assert handoff_payload["handoff_status"] == "contract_failed"
    assert handoff_payload["handoff_action"] == "hold"
    assert handoff_payload["should_trigger_release"] is False
    assert handoff_payload["release_exit_code"] == 1
    assert "should_promote_mismatch_passed" in handoff_payload["structural_issues"]


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_release_handoff_gate_module()
    payload = _sample_terminal_publish_payload()
    payload["publish_status"] = "failed"
    payload["publish_exit_code"] = 1
    payload["should_promote"] = False
    payload["completion_status"] = "run_completed_failure"
    payload["completion_exit_code"] = 1
    payload["reason_codes"] = ["run_completed_with_failure"]

    report_path = tmp_path / "ci_workflow_terminal_publish_failed.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_terminal_publish_report(report_path)
    handoff_payload = gate.build_release_handoff_payload(
        report,
        source_path=report_path.resolve(),
        target_environment="staging",
        release_channel="canary",
    )
    outputs = gate.build_github_output_values(
        handoff_payload,
        output_json=Path(".claude/reports/linux_unified_gate/ci_workflow_release_handoff.json"),
        output_markdown=Path(".claude/reports/linux_unified_gate/ci_workflow_release_handoff.md"),
    )

    assert outputs["workflow_release_handoff_status"] == "failed"
    assert outputs["workflow_release_handoff_action"] == "reject"
    assert outputs["workflow_release_handoff_should_trigger_release"] == "false"
    assert outputs["workflow_release_handoff_release_exit_code"] == "1"
    assert outputs["workflow_release_handoff_target_environment"] == "staging"
    assert outputs["workflow_release_handoff_release_channel"] == "canary"
    assert outputs["workflow_release_handoff_publish_status"] == "failed"
    assert outputs["workflow_release_handoff_completion_status"] == "run_completed_failure"
    assert outputs["workflow_release_handoff_run_id"] == "1234567890"
    assert outputs["workflow_release_handoff_report_json"].endswith(
        "ci_workflow_release_handoff.json"
    )
    assert outputs["workflow_release_handoff_report_markdown"].endswith(
        "ci_workflow_release_handoff.md"
    )

"""Contract tests for P2-35 Linux CI workflow release finalization gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_release_finalization_gate_module():
    script_path = Path("scripts") / "run_p2_linux_ci_workflow_release_finalization_gate.py"
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_release_finalization_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_release_terminal_publish_payload() -> dict:
    return {
        "generated_at": "2026-04-30T00:00:00+00:00",
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
        "should_finalize_release": True,
        "release_terminal_publish_summary": (
            "release_completion_status=release_run_completed_success "
            "release_publish_status=passed should_finalize_release=True"
        ),
        "allow_in_progress": False,
        "should_poll_release_run": True,
        "release_run_id": 2233445566,
        "release_run_url": "https://github.com/acme/demo/actions/runs/2233445566",
        "reason_codes": ["release_completed_success"],
        "failed_checks": [],
        "structural_issues": [],
        "missing_artifacts": [],
    }


def test_build_release_finalization_payload_marks_finalize(tmp_path: Path):
    gate = _load_ci_workflow_release_finalization_gate_module()
    payload = _sample_release_terminal_publish_payload()
    report_path = tmp_path / "ci_workflow_release_terminal_publish.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_terminal_publish_report(report_path)
    finalization_payload = gate.build_release_finalization_payload(
        report,
        source_path=report_path.resolve(),
        hold_policy="pass",
    )

    assert finalization_payload["release_finalization_status"] == "finalized"
    assert finalization_payload["release_finalization_decision"] == "finalize"
    assert finalization_payload["should_finalize_release"] is True
    assert finalization_payload["release_finalization_exit_code"] == 0
    assert finalization_payload["reason_codes"] == ["release_finalized"]


def test_build_release_finalization_payload_hold_fail_policy(tmp_path: Path):
    gate = _load_ci_workflow_release_finalization_gate_module()
    payload = _sample_release_terminal_publish_payload()
    payload["release_tracking_status"] = "release_run_in_progress"
    payload["release_completion_status"] = "release_run_await_timeout"
    payload["release_publish_status"] = "in_progress"
    payload["release_publish_exit_code"] = 0
    payload["should_finalize_release"] = False
    payload["reason_codes"] = ["release_run_await_timeout"]

    report_path = tmp_path / "ci_workflow_release_terminal_publish_in_progress.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_terminal_publish_report(report_path)
    finalization_payload = gate.build_release_finalization_payload(
        report,
        source_path=report_path.resolve(),
        hold_policy="fail",
    )

    assert finalization_payload["release_finalization_status"] == "awaiting_release"
    assert finalization_payload["release_finalization_decision"] == "hold"
    assert finalization_payload["should_finalize_release"] is False
    assert finalization_payload["release_finalization_exit_code"] == 1
    assert "on_hold_policy_fail" in finalization_payload["reason_codes"]


def test_build_release_finalization_payload_rejects_contract_mismatch(tmp_path: Path):
    gate = _load_ci_workflow_release_finalization_gate_module()
    payload = _sample_release_terminal_publish_payload()
    payload["release_publish_status"] = "passed"
    payload["release_publish_exit_code"] = 1
    payload["should_finalize_release"] = True

    report_path = tmp_path / "ci_workflow_release_terminal_publish_mismatch.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_terminal_publish_report(report_path)
    finalization_payload = gate.build_release_finalization_payload(
        report,
        source_path=report_path.resolve(),
        hold_policy="pass",
    )

    assert finalization_payload["release_finalization_status"] == "contract_failed"
    assert finalization_payload["release_finalization_decision"] == "abort"
    assert finalization_payload["release_finalization_exit_code"] == 1
    assert "release_publish_exit_code_mismatch_passed" in finalization_payload["structural_issues"]


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_release_finalization_gate_module()
    payload = _sample_release_terminal_publish_payload()
    payload["release_publish_status"] = "failed"
    payload["release_publish_exit_code"] = 1
    payload["should_finalize_release"] = False
    payload["reason_codes"] = ["release_run_completed_with_failure"]

    report_path = tmp_path / "ci_workflow_release_terminal_publish_failed.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_terminal_publish_report(report_path)
    finalization_payload = gate.build_release_finalization_payload(
        report,
        source_path=report_path.resolve(),
        hold_policy="pass",
    )
    outputs = gate.build_github_output_values(
        finalization_payload,
        output_json=Path(".claude/reports/linux_unified_gate/ci_workflow_release_finalization.json"),
        output_markdown=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_finalization.md"
        ),
    )

    assert outputs["workflow_release_finalization_status"] == "failed"
    assert outputs["workflow_release_finalization_decision"] == "abort"
    assert outputs["workflow_release_finalization_should_finalize_release"] == "false"
    assert outputs["workflow_release_finalization_exit_code"] == "1"
    assert outputs["workflow_release_finalization_publish_status"] == "failed"
    assert outputs["workflow_release_finalization_run_id"] == "2233445566"
    assert outputs["workflow_release_finalization_run_url"].endswith("/actions/runs/2233445566")
    assert outputs["workflow_release_finalization_report_json"].endswith(
        "ci_workflow_release_finalization.json"
    )
    assert outputs["workflow_release_finalization_report_markdown"].endswith(
        "ci_workflow_release_finalization.md"
    )

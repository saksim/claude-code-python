"""Contract tests for P2-29 Linux CI workflow terminal publish gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_terminal_publish_gate_module():
    script_path = Path("scripts") / "run_p2_linux_ci_workflow_terminal_publish_gate.py"
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_terminal_publish_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_dispatch_completion_payload() -> dict:
    return {
        "generated_at": "2026-04-30T00:00:00+00:00",
        "source_dispatch_trace_report": "/tmp/ci_workflow_dispatch_trace.json",
        "source_dispatch_execution_report": "/tmp/ci_workflow_dispatch_execution.json",
        "source_dispatch_report": "/tmp/ci_workflow_dispatch.json",
        "project_root": "/tmp",
        "execution_status": "dispatched",
        "tracking_status": "run_completed_success",
        "completion_status": "run_completed_success",
        "completion_exit_code": 0,
        "dry_run": False,
        "allow_in_progress": False,
        "should_poll_workflow_run": True,
        "run_id": 1234567890,
        "run_url": "https://github.com/acme/demo/actions/runs/1234567890",
        "reason_codes": ["run_completed_success"],
        "failed_checks": [],
        "structural_issues": [],
        "missing_artifacts": [],
    }


def test_build_terminal_publish_payload_marks_passed_and_promotable(tmp_path: Path):
    gate = _load_ci_workflow_terminal_publish_gate_module()
    payload = _sample_dispatch_completion_payload()
    report_path = tmp_path / "ci_workflow_dispatch_completion.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_dispatch_completion_report(report_path)
    publish_payload = gate.build_terminal_publish_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert publish_payload["publish_status"] == "passed"
    assert publish_payload["publish_exit_code"] == 0
    assert publish_payload["should_promote"] is True
    assert publish_payload["reason_codes"] == ["workflow_completed_success"]


def test_build_terminal_publish_payload_timeout_with_allow_in_progress_becomes_in_progress(
    tmp_path: Path,
):
    gate = _load_ci_workflow_terminal_publish_gate_module()
    payload = _sample_dispatch_completion_payload()
    payload["tracking_status"] = "run_in_progress"
    payload["completion_status"] = "run_await_timeout"
    payload["completion_exit_code"] = 0
    payload["allow_in_progress"] = True
    payload["reason_codes"] = ["run_await_timeout"]

    report_path = tmp_path / "ci_workflow_dispatch_completion_timeout.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_dispatch_completion_report(report_path)
    publish_payload = gate.build_terminal_publish_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert publish_payload["publish_status"] == "in_progress"
    assert publish_payload["publish_exit_code"] == 0
    assert publish_payload["should_promote"] is False
    assert "run_await_timeout" in publish_payload["reason_codes"]


def test_build_terminal_publish_payload_rejects_completion_contract_mismatch(tmp_path: Path):
    gate = _load_ci_workflow_terminal_publish_gate_module()
    payload = _sample_dispatch_completion_payload()
    payload["completion_status"] = "run_completed_success"
    payload["completion_exit_code"] = 1

    report_path = tmp_path / "ci_workflow_dispatch_completion_mismatch.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_dispatch_completion_report(report_path)
    publish_payload = gate.build_terminal_publish_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert publish_payload["publish_status"] == "contract_failed"
    assert publish_payload["publish_exit_code"] == 1
    assert publish_payload["should_promote"] is False
    assert "completion_exit_code_mismatch_success" in publish_payload["structural_issues"]


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_terminal_publish_gate_module()
    payload = _sample_dispatch_completion_payload()
    payload["completion_status"] = "run_completed_failure"
    payload["completion_exit_code"] = 1
    payload["reason_codes"] = ["run_completed_with_failure"]

    report_path = tmp_path / "ci_workflow_dispatch_completion_failed.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_dispatch_completion_report(report_path)
    publish_payload = gate.build_terminal_publish_payload(
        report,
        source_path=report_path.resolve(),
    )
    outputs = gate.build_github_output_values(
        publish_payload,
        output_json=Path(".claude/reports/linux_unified_gate/ci_workflow_terminal_publish.json"),
        output_markdown=Path(".claude/reports/linux_unified_gate/ci_workflow_terminal_publish.md"),
    )

    assert outputs["workflow_terminal_publish_status"] == "failed"
    assert outputs["workflow_terminal_publish_exit_code"] == "1"
    assert outputs["workflow_terminal_publish_should_promote"] == "false"
    assert outputs["workflow_terminal_publish_completion_status"] == "run_completed_failure"
    assert outputs["workflow_terminal_publish_run_id"] == "1234567890"
    assert outputs["workflow_terminal_publish_report_json"].endswith(
        "ci_workflow_terminal_publish.json"
    )
    assert outputs["workflow_terminal_publish_report_markdown"].endswith(
        "ci_workflow_terminal_publish.md"
    )


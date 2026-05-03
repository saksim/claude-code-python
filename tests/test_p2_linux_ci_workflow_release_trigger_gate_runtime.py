"""Contract tests for P2-31 Linux CI workflow release trigger gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_release_trigger_gate_module():
    script_path = Path("scripts") / "run_p2_linux_ci_workflow_release_trigger_gate.py"
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_release_trigger_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_release_handoff_payload() -> dict:
    return {
        "generated_at": "2026-04-30T00:00:00+00:00",
        "source_terminal_publish_report": "/tmp/ci_workflow_terminal_publish.json",
        "source_dispatch_completion_report": "/tmp/ci_workflow_dispatch_completion.json",
        "source_dispatch_trace_report": "/tmp/ci_workflow_dispatch_trace.json",
        "source_dispatch_execution_report": "/tmp/ci_workflow_dispatch_execution.json",
        "source_dispatch_report": "/tmp/ci_workflow_dispatch.json",
        "target_environment": "production",
        "release_channel": "stable",
        "publish_status": "passed",
        "publish_exit_code": 0,
        "should_promote": True,
        "completion_status": "run_completed_success",
        "completion_exit_code": 0,
        "handoff_status": "ready_for_release",
        "handoff_action": "promote",
        "should_trigger_release": True,
        "release_exit_code": 0,
        "handoff_summary": (
            "publish_status=passed handoff_status=ready_for_release "
            "should_trigger_release=True target_environment=production "
            "release_channel=stable"
        ),
        "publish_summary": (
            "completion_status=run_completed_success publish_status=passed "
            "should_promote=True"
        ),
        "run_id": 1234567890,
        "run_url": "https://github.com/acme/demo/actions/runs/1234567890",
        "reason_codes": ["release_ready"],
        "failed_checks": [],
        "structural_issues": [],
        "missing_artifacts": [],
    }


def test_build_release_trigger_payload_ready_dry_run(tmp_path: Path):
    gate = _load_ci_workflow_release_trigger_gate_module()
    payload = _sample_release_handoff_payload()
    report_path = tmp_path / "ci_workflow_release_handoff.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_handoff_report(report_path)
    command_parts = gate.build_release_command_parts(
        report,
        source_report_path=report_path.resolve(),
        gh_executable="gh",
        release_workflow_path=".github/workflows/release.yml",
        release_workflow_ref="main",
        release_command="",
    )
    trigger_payload = gate.build_release_trigger_payload(
        report,
        source_path=report_path.resolve(),
        project_root=tmp_path.resolve(),
        release_command_parts=command_parts,
        release_workflow_path=".github/workflows/release.yml",
        release_workflow_ref="main",
        dry_run=True,
        command_result=None,
    )

    assert trigger_payload["release_trigger_status"] == "ready_dry_run"
    assert trigger_payload["release_trigger_exit_code"] == 0
    assert trigger_payload["release_trigger_attempted"] is False
    assert trigger_payload["should_trigger_release"] is True
    assert trigger_payload["release_command_parts"][:3] == ["gh", "workflow", "run"]


def test_build_release_trigger_payload_awaiting_completion_passthrough(tmp_path: Path):
    gate = _load_ci_workflow_release_trigger_gate_module()
    payload = _sample_release_handoff_payload()
    payload["handoff_status"] = "awaiting_completion"
    payload["handoff_action"] = "hold"
    payload["should_trigger_release"] = False
    payload["release_exit_code"] = 0
    payload["publish_status"] = "in_progress"
    payload["completion_status"] = "run_await_timeout"
    payload["reason_codes"] = ["run_await_timeout"]

    report_path = tmp_path / "ci_workflow_release_handoff_waiting.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_handoff_report(report_path)
    trigger_payload = gate.build_release_trigger_payload(
        report,
        source_path=report_path.resolve(),
        project_root=tmp_path.resolve(),
        release_command_parts=[],
        release_workflow_path=".github/workflows/release.yml",
        release_workflow_ref="main",
        dry_run=False,
        command_result=None,
    )

    assert trigger_payload["release_trigger_status"] == "awaiting_completion"
    assert trigger_payload["release_trigger_exit_code"] == 0
    assert trigger_payload["release_trigger_attempted"] is False
    assert trigger_payload["should_trigger_release"] is False


def test_load_release_handoff_report_rejects_contract_mismatch(tmp_path: Path):
    gate = _load_ci_workflow_release_trigger_gate_module()
    payload = _sample_release_handoff_payload()
    payload["handoff_status"] = "ready_for_release"
    payload["handoff_action"] = "promote"
    payload["should_trigger_release"] = False
    payload["release_exit_code"] = 0
    report_path = tmp_path / "ci_workflow_release_handoff_bad_contract.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    try:
        gate.load_release_handoff_report(report_path)
        raised = False
    except ValueError:
        raised = True

    assert raised


def test_build_release_trigger_payload_marks_failed_command(tmp_path: Path):
    gate = _load_ci_workflow_release_trigger_gate_module()
    payload = _sample_release_handoff_payload()
    report_path = tmp_path / "ci_workflow_release_handoff.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_handoff_report(report_path)
    command_parts = gate.build_release_command_parts(
        report,
        source_report_path=report_path.resolve(),
        gh_executable="gh",
        release_workflow_path=".github/workflows/release.yml",
        release_workflow_ref="main",
        release_command="",
    )
    trigger_payload = gate.build_release_trigger_payload(
        report,
        source_path=report_path.resolve(),
        project_root=tmp_path.resolve(),
        release_command_parts=command_parts,
        release_workflow_path=".github/workflows/release.yml",
        release_workflow_ref="main",
        dry_run=False,
        command_result={
            "attempted": True,
            "returncode": 1,
            "stdout_tail": "",
            "stderr_tail": "release dispatch failed",
            "error_type": "",
            "error_message": "",
        },
    )

    assert trigger_payload["release_trigger_status"] == "trigger_failed"
    assert trigger_payload["release_trigger_exit_code"] == 1
    assert trigger_payload["release_trigger_attempted"] is True
    assert "release_trigger_command_failed" in trigger_payload["reason_codes"]


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_release_trigger_gate_module()
    payload = _sample_release_handoff_payload()
    report_path = tmp_path / "ci_workflow_release_handoff.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = gate.load_release_handoff_report(report_path)
    command_parts = gate.build_release_command_parts(
        report,
        source_report_path=report_path.resolve(),
        gh_executable="gh",
        release_workflow_path=".github/workflows/release.yml",
        release_workflow_ref="main",
        release_command="",
    )
    trigger_payload = gate.build_release_trigger_payload(
        report,
        source_path=report_path.resolve(),
        project_root=tmp_path.resolve(),
        release_command_parts=command_parts,
        release_workflow_path=".github/workflows/release.yml",
        release_workflow_ref="main",
        dry_run=True,
        command_result=None,
    )
    outputs = gate.build_github_output_values(
        trigger_payload,
        output_json=Path(".claude/reports/linux_unified_gate/ci_workflow_release_trigger.json"),
        output_markdown=Path(".claude/reports/linux_unified_gate/ci_workflow_release_trigger.md"),
    )

    assert outputs["workflow_release_trigger_status"] == "ready_dry_run"
    assert outputs["workflow_release_trigger_should_trigger_release"] == "true"
    assert outputs["workflow_release_trigger_attempted"] == "false"
    assert outputs["workflow_release_trigger_exit_code"] == "0"
    assert outputs["workflow_release_trigger_target_environment"] == "production"
    assert outputs["workflow_release_trigger_release_channel"] == "stable"
    assert outputs["workflow_release_trigger_handoff_status"] == "ready_for_release"
    assert outputs["workflow_release_trigger_run_id"] == "1234567890"
    assert outputs["workflow_release_trigger_run_url"].endswith("/1234567890")
    assert outputs["workflow_release_trigger_report_json"].endswith(
        "ci_workflow_release_trigger.json"
    )
    assert outputs["workflow_release_trigger_report_markdown"].endswith(
        "ci_workflow_release_trigger.md"
    )

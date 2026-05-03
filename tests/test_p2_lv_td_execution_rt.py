"""Contract tests for P2-70 Linux CI workflow Linux validation terminal dispatch execution gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_linux_validation_terminal_dispatch_execution_gate_module():
    script_path = (
        Path("scripts")
        / "run_p2_lv_td_execution_gate.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_linux_validation_terminal_dispatch_execution_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_linux_validation_terminal_dispatch_payload() -> dict:
    return {
        "generated_at": "2026-05-02T00:00:00+00:00",
        "source_linux_validation_terminal_verdict_publish_report": "/tmp/ci_workflow_linux_validation_terminal_verdict_publish.json",
        "source_linux_validation_terminal_verdict_report": "/tmp/ci_workflow_linux_validation_terminal_verdict.json",
        "source_linux_validation_dispatch_report": "/tmp/ci_workflow_linux_validation_dispatch.json",
        "source_linux_validation_final_publish_archive_report": "/tmp/ci_workflow_linux_validation_final_publish_archive.json",
        "project_root": "/tmp",
        "source_terminal_verdict_report": "/tmp/ci_workflow_terminal_verdict.json",
        "source_release_final_publish_archive_report": "/tmp/ci_workflow_release_final_publish_archive.json",
        "source_gate_manifest_drift_report": "/tmp/linux_gate_manifest_drift.json",
        "release_final_publish_archive_status": "archived",
        "gate_manifest_drift_status": "passed",
        "gate_manifest_drift_missing_runtime_tests": [],
        "gate_manifest_drift_missing_manifest_entries": [],
        "gate_manifest_drift_orphan_manifest_entries": [],
        "terminal_verdict_status": "ready_for_linux_validation",
        "terminal_verdict_decision": "proceed_linux_validation",
        "terminal_verdict_exit_code": 0,
        "terminal_verdict_should_proceed": True,
        "terminal_verdict_requires_manual_action": False,
        "terminal_verdict_channel": "release",
        "linux_validation_should_dispatch": True,
        "linux_validation_requires_manual_action": False,
        "linux_validation_channel": "release",
        "linux_validation_dispatch_status": "ready_dry_run",
        "linux_validation_dispatch_decision": "dispatch_linux_validation",
        "linux_validation_dispatch_exit_code": 0,
        "linux_validation_dispatch_attempted": False,
        "linux_validation_dispatch_command_returncode": None,
        "linux_validation_terminal_verdict_status": "ready_for_linux_validation",
        "linux_validation_terminal_verdict_decision": "proceed_linux_validation",
        "linux_validation_terminal_verdict_exit_code": 0,
        "linux_validation_terminal_verdict_should_proceed": True,
        "linux_validation_terminal_verdict_requires_manual_action": False,
        "linux_validation_terminal_verdict_channel": "release",
        "linux_validation_terminal_verdict_publish_status": "published",
        "linux_validation_terminal_verdict_publish_decision": "announce_linux_validation_terminal_ready",
        "linux_validation_terminal_verdict_publish_exit_code": 0,
        "linux_validation_terminal_verdict_publish_should_notify": True,
        "linux_validation_terminal_verdict_publish_requires_manual_action": False,
        "linux_validation_terminal_verdict_publish_channel": "release",
        "linux_validation_terminal_verdict_publish_summary": (
            "linux_validation_terminal_verdict_status=ready_for_linux_validation "
            "linux_validation_terminal_verdict_publish_status=published "
            "linux_validation_terminal_verdict_publish_decision=announce_linux_validation_terminal_ready"
        ),
        "dry_run": True,
        "verdict_command_returncode": None,
        "verdict_command_stdout_tail": "",
        "verdict_command_stderr_tail": "",
        "verdict_error_type": "",
        "verdict_error_message": "",
        "release_run_id": 1234567890,
        "release_run_url": "https://github.com/acme/demo/actions/runs/1234567890",
        "follow_up_queue_url": "",
        "linux_validation_dispatch_summary": (
            "terminal_verdict_status=ready_for_linux_validation "
            "terminal_verdict_decision=proceed_linux_validation "
            "linux_validation_dispatch_status=ready_dry_run "
            "linux_validation_dispatch_decision=dispatch_linux_validation"
        ),
        "linux_validation_terminal_verdict_summary": (
            "linux_validation_final_publish_archive_status=archived "
            "linux_validation_terminal_verdict_status=ready_for_linux_validation "
            "linux_validation_terminal_verdict_decision=proceed_linux_validation"
        ),
        "linux_validation_terminal_dispatch_status": "ready_dry_run",
        "linux_validation_terminal_dispatch_decision": "dispatch_linux_validation_terminal",
        "linux_validation_terminal_dispatch_exit_code": 0,
        "linux_validation_terminal_should_dispatch": True,
        "linux_validation_terminal_dispatch_requires_manual_action": False,
        "linux_validation_terminal_dispatch_channel": "release",
        "linux_validation_terminal_dispatch_summary": (
            "linux_validation_terminal_verdict_publish_status=published "
            "linux_validation_terminal_dispatch_status=ready_dry_run "
            "linux_validation_terminal_dispatch_decision=dispatch_linux_validation_terminal"
        ),
        "reason_codes": ["linux_validation_terminal_dispatch_ready_dry_run"],
        "structural_issues": [],
        "missing_artifacts": [],
        "evidence_manifest": [
            {
                "source": "dispatch",
                "path": "/tmp/ci_workflow_linux_validation_dispatch.json",
                "exists": True,
            },
            {
                "source": "terminal_dispatch",
                "path": "/tmp/ci_workflow_linux_validation_terminal_dispatch.json",
                "exists": True,
            },
        ],
    }


def test_build_linux_validation_terminal_dispatch_execution_payload_ready_dry_run(tmp_path: Path):
    gate = _load_ci_workflow_linux_validation_terminal_dispatch_execution_gate_module()
    dispatch_payload = _sample_linux_validation_terminal_dispatch_payload()

    report_path = tmp_path / "ci_workflow_linux_validation_terminal_dispatch.json"
    report_path.write_text(json.dumps(dispatch_payload, indent=2), encoding="utf-8")

    dispatch_report = gate.load_linux_validation_terminal_dispatch_report(report_path)
    command_parts = gate.build_linux_validation_terminal_command_parts(
        terminal_dispatch_report=dispatch_report,
        python_executable="python",
        linux_validation_terminal_command="",
    )
    payload = gate.build_linux_validation_terminal_dispatch_execution_payload(
        dispatch_report,
        source_path=report_path.resolve(),
        project_root=tmp_path,
        linux_validation_terminal_timeout_seconds=7200,
        command_parts=command_parts,
        dry_run=True,
        command_result=None,
    )

    assert payload["linux_validation_terminal_dispatch_execution_status"] == "ready_dry_run"
    assert (
        payload["linux_validation_terminal_dispatch_execution_decision"]
        == "dispatch_linux_validation_terminal"
    )
    assert payload["linux_validation_terminal_dispatch_execution_exit_code"] == 0
    assert payload["linux_validation_terminal_dispatch_attempted"] is False
    assert payload["linux_validation_terminal_should_dispatch"] is True
    assert payload["linux_validation_terminal_dispatch_execution_channel"] == "release"
    assert payload["linux_validation_terminal_command_parts"][:2] == ["python", "scripts/run_p2_linux_unified_pipeline_gate.py"]


def test_build_linux_validation_terminal_dispatch_execution_payload_dispatched_with_follow_up(
    tmp_path: Path,
):
    gate = _load_ci_workflow_linux_validation_terminal_dispatch_execution_gate_module()
    dispatch_payload = _sample_linux_validation_terminal_dispatch_payload()
    dispatch_payload["terminal_verdict_status"] = "ready_with_follow_up_for_linux_validation"
    dispatch_payload["terminal_verdict_decision"] = "proceed_linux_validation_with_follow_up"
    dispatch_payload["terminal_verdict_exit_code"] = 1
    dispatch_payload["terminal_verdict_channel"] = "follow_up"
    dispatch_payload["linux_validation_channel"] = "follow_up"
    dispatch_payload["linux_validation_dispatch_status"] = "ready_with_follow_up_dry_run"
    dispatch_payload["linux_validation_dispatch_decision"] = "dispatch_linux_validation_with_follow_up"
    dispatch_payload["linux_validation_dispatch_exit_code"] = 1
    dispatch_payload["linux_validation_terminal_verdict_status"] = "ready_with_follow_up_for_linux_validation"
    dispatch_payload["linux_validation_terminal_verdict_decision"] = "proceed_linux_validation_with_follow_up"
    dispatch_payload["linux_validation_terminal_verdict_exit_code"] = 1
    dispatch_payload["linux_validation_terminal_verdict_channel"] = "follow_up"
    dispatch_payload["linux_validation_terminal_verdict_publish_status"] = "published_with_follow_up"
    dispatch_payload["linux_validation_terminal_verdict_publish_decision"] = (
        "announce_linux_validation_terminal_ready_with_follow_up"
    )
    dispatch_payload["linux_validation_terminal_verdict_publish_exit_code"] = 1
    dispatch_payload["linux_validation_terminal_verdict_publish_channel"] = "follow_up"
    dispatch_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    dispatch_payload["linux_validation_terminal_dispatch_status"] = "ready_with_follow_up_dry_run"
    dispatch_payload["linux_validation_terminal_dispatch_decision"] = (
        "dispatch_linux_validation_terminal_with_follow_up"
    )
    dispatch_payload["linux_validation_terminal_dispatch_exit_code"] = 1
    dispatch_payload["linux_validation_terminal_dispatch_channel"] = "follow_up"
    dispatch_payload["reason_codes"] = [
        "linux_validation_terminal_dispatch_ready_with_follow_up_dry_run"
    ]

    report_path = tmp_path / "ci_workflow_linux_validation_terminal_dispatch_follow_up.json"
    report_path.write_text(json.dumps(dispatch_payload, indent=2), encoding="utf-8")

    dispatch_report = gate.load_linux_validation_terminal_dispatch_report(report_path)
    command_parts = gate.build_linux_validation_terminal_command_parts(
        terminal_dispatch_report=dispatch_report,
        python_executable="python",
        linux_validation_terminal_command="",
    )
    payload = gate.build_linux_validation_terminal_dispatch_execution_payload(
        dispatch_report,
        source_path=report_path.resolve(),
        project_root=tmp_path,
        linux_validation_terminal_timeout_seconds=7200,
        command_parts=command_parts,
        dry_run=False,
        command_result={
            "attempted": True,
            "returncode": 0,
            "stdout_tail": "ok",
            "stderr_tail": "",
            "error_type": "",
            "error_message": "",
        },
    )

    assert payload["linux_validation_terminal_dispatch_execution_status"] == "dispatched"
    assert (
        payload["linux_validation_terminal_dispatch_execution_decision"]
        == "dispatch_linux_validation_terminal_with_follow_up"
    )
    assert payload["linux_validation_terminal_dispatch_execution_exit_code"] == 1
    assert payload["linux_validation_terminal_dispatch_attempted"] is True
    assert payload["linux_validation_terminal_dispatch_execution_requires_manual_action"] is False
    assert payload["linux_validation_terminal_dispatch_execution_channel"] == "follow_up"
    assert payload["follow_up_queue_url"].endswith("/issues/77")
    assert "linux_validation_terminal_dispatch_execution_command_succeeded" in payload["reason_codes"]


def test_build_linux_validation_terminal_dispatch_execution_payload_blocked(tmp_path: Path):
    gate = _load_ci_workflow_linux_validation_terminal_dispatch_execution_gate_module()
    dispatch_payload = _sample_linux_validation_terminal_dispatch_payload()
    dispatch_payload["terminal_verdict_status"] = "blocked"
    dispatch_payload["terminal_verdict_decision"] = "halt_linux_validation_blocker"
    dispatch_payload["terminal_verdict_exit_code"] = 1
    dispatch_payload["terminal_verdict_should_proceed"] = False
    dispatch_payload["terminal_verdict_requires_manual_action"] = True
    dispatch_payload["terminal_verdict_channel"] = "blocker"
    dispatch_payload["linux_validation_should_dispatch"] = False
    dispatch_payload["linux_validation_requires_manual_action"] = True
    dispatch_payload["linux_validation_channel"] = "blocker"
    dispatch_payload["linux_validation_dispatch_status"] = "blocked"
    dispatch_payload["linux_validation_dispatch_decision"] = "hold_linux_validation_blocker"
    dispatch_payload["linux_validation_dispatch_exit_code"] = 1
    dispatch_payload["linux_validation_terminal_verdict_status"] = "blocked"
    dispatch_payload["linux_validation_terminal_verdict_decision"] = "halt_linux_validation_blocker"
    dispatch_payload["linux_validation_terminal_verdict_exit_code"] = 1
    dispatch_payload["linux_validation_terminal_verdict_should_proceed"] = False
    dispatch_payload["linux_validation_terminal_verdict_requires_manual_action"] = True
    dispatch_payload["linux_validation_terminal_verdict_channel"] = "blocker"
    dispatch_payload["linux_validation_terminal_verdict_publish_status"] = "blocked"
    dispatch_payload["linux_validation_terminal_verdict_publish_decision"] = (
        "announce_linux_validation_terminal_blocker"
    )
    dispatch_payload["linux_validation_terminal_verdict_publish_exit_code"] = 1
    dispatch_payload["linux_validation_terminal_verdict_publish_requires_manual_action"] = True
    dispatch_payload["linux_validation_terminal_verdict_publish_channel"] = "blocker"
    dispatch_payload["linux_validation_terminal_dispatch_status"] = "blocked"
    dispatch_payload["linux_validation_terminal_dispatch_decision"] = (
        "hold_linux_validation_terminal_blocker"
    )
    dispatch_payload["linux_validation_terminal_dispatch_exit_code"] = 1
    dispatch_payload["linux_validation_terminal_should_dispatch"] = False
    dispatch_payload["linux_validation_terminal_dispatch_requires_manual_action"] = True
    dispatch_payload["linux_validation_terminal_dispatch_channel"] = "blocker"
    dispatch_payload["reason_codes"] = ["linux_validation_terminal_dispatch_blocked"]

    report_path = tmp_path / "ci_workflow_linux_validation_terminal_dispatch_blocked.json"
    report_path.write_text(json.dumps(dispatch_payload, indent=2), encoding="utf-8")

    dispatch_report = gate.load_linux_validation_terminal_dispatch_report(report_path)
    command_parts = gate.build_linux_validation_terminal_command_parts(
        terminal_dispatch_report=dispatch_report,
        python_executable="python",
        linux_validation_terminal_command="",
    )
    payload = gate.build_linux_validation_terminal_dispatch_execution_payload(
        dispatch_report,
        source_path=report_path.resolve(),
        project_root=tmp_path,
        linux_validation_terminal_timeout_seconds=7200,
        command_parts=command_parts,
        dry_run=False,
        command_result=None,
    )

    assert payload["linux_validation_terminal_dispatch_execution_status"] == "blocked"
    assert (
        payload["linux_validation_terminal_dispatch_execution_decision"]
        == "hold_linux_validation_terminal_blocker"
    )
    assert payload["linux_validation_terminal_dispatch_execution_exit_code"] == 1
    assert payload["linux_validation_terminal_dispatch_attempted"] is False
    assert payload["linux_validation_terminal_dispatch_execution_requires_manual_action"] is True
    assert payload["linux_validation_terminal_dispatch_execution_channel"] == "blocker"
    assert "linux_validation_terminal_dispatch_execution_blocked" in payload["reason_codes"]


def test_build_linux_validation_terminal_dispatch_execution_payload_rejects_contract_mismatch(
    tmp_path: Path,
):
    gate = _load_ci_workflow_linux_validation_terminal_dispatch_execution_gate_module()
    dispatch_payload = _sample_linux_validation_terminal_dispatch_payload()
    dispatch_payload["linux_validation_terminal_dispatch_status"] = "ready_dry_run"
    dispatch_payload["linux_validation_terminal_dispatch_decision"] = (
        "dispatch_linux_validation_terminal_with_follow_up"
    )

    report_path = tmp_path / "ci_workflow_linux_validation_terminal_dispatch_mismatch.json"
    report_path.write_text(json.dumps(dispatch_payload, indent=2), encoding="utf-8")

    try:
        gate.load_linux_validation_terminal_dispatch_report(report_path)
        raised = False
    except ValueError:
        raised = True

    assert raised


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_linux_validation_terminal_dispatch_execution_gate_module()
    dispatch_payload = _sample_linux_validation_terminal_dispatch_payload()
    dispatch_payload["terminal_verdict_status"] = "ready_with_follow_up_for_linux_validation"
    dispatch_payload["terminal_verdict_decision"] = "proceed_linux_validation_with_follow_up"
    dispatch_payload["terminal_verdict_exit_code"] = 1
    dispatch_payload["terminal_verdict_channel"] = "follow_up"
    dispatch_payload["linux_validation_channel"] = "follow_up"
    dispatch_payload["linux_validation_dispatch_status"] = "ready_with_follow_up_dry_run"
    dispatch_payload["linux_validation_dispatch_decision"] = "dispatch_linux_validation_with_follow_up"
    dispatch_payload["linux_validation_dispatch_exit_code"] = 1
    dispatch_payload["linux_validation_terminal_verdict_status"] = "ready_with_follow_up_for_linux_validation"
    dispatch_payload["linux_validation_terminal_verdict_decision"] = "proceed_linux_validation_with_follow_up"
    dispatch_payload["linux_validation_terminal_verdict_exit_code"] = 1
    dispatch_payload["linux_validation_terminal_verdict_channel"] = "follow_up"
    dispatch_payload["linux_validation_terminal_verdict_publish_status"] = "published_with_follow_up"
    dispatch_payload["linux_validation_terminal_verdict_publish_decision"] = (
        "announce_linux_validation_terminal_ready_with_follow_up"
    )
    dispatch_payload["linux_validation_terminal_verdict_publish_exit_code"] = 1
    dispatch_payload["linux_validation_terminal_verdict_publish_channel"] = "follow_up"
    dispatch_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    dispatch_payload["linux_validation_terminal_dispatch_status"] = "ready_with_follow_up_dry_run"
    dispatch_payload["linux_validation_terminal_dispatch_decision"] = (
        "dispatch_linux_validation_terminal_with_follow_up"
    )
    dispatch_payload["linux_validation_terminal_dispatch_exit_code"] = 1
    dispatch_payload["linux_validation_terminal_dispatch_channel"] = "follow_up"
    dispatch_payload["reason_codes"] = [
        "linux_validation_terminal_dispatch_ready_with_follow_up_dry_run"
    ]

    report_path = tmp_path / "ci_workflow_linux_validation_terminal_dispatch_output.json"
    report_path.write_text(json.dumps(dispatch_payload, indent=2), encoding="utf-8")

    dispatch_report = gate.load_linux_validation_terminal_dispatch_report(report_path)
    command_parts = gate.build_linux_validation_terminal_command_parts(
        terminal_dispatch_report=dispatch_report,
        python_executable="python",
        linux_validation_terminal_command="",
    )
    payload = gate.build_linux_validation_terminal_dispatch_execution_payload(
        dispatch_report,
        source_path=report_path.resolve(),
        project_root=tmp_path,
        linux_validation_terminal_timeout_seconds=7200,
        command_parts=command_parts,
        dry_run=True,
        command_result=None,
    )
    outputs = gate.build_github_output_values(
        payload,
        output_json=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_execution.json"
        ),
        output_markdown=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_execution.md"
        ),
    )

    assert outputs["workflow_linux_validation_terminal_dispatch_execution_status"] == (
        "ready_with_follow_up_dry_run"
    )
    assert outputs["workflow_linux_validation_terminal_dispatch_execution_decision"] == (
        "dispatch_linux_validation_terminal_with_follow_up"
    )
    assert outputs["workflow_linux_validation_terminal_dispatch_execution_exit_code"] == "1"
    assert outputs["workflow_linux_validation_terminal_dispatch_execution_should_dispatch"] == "true"
    assert outputs["workflow_linux_validation_terminal_dispatch_execution_attempted"] == "false"
    assert (
        outputs["workflow_linux_validation_terminal_dispatch_execution_requires_manual_action"]
        == "false"
    )
    assert outputs["workflow_linux_validation_terminal_dispatch_execution_channel"] == "follow_up"
    assert outputs["workflow_linux_validation_terminal_dispatch_execution_follow_up_queue_url"].endswith(
        "/issues/77"
    )
    assert outputs["workflow_linux_validation_terminal_dispatch_execution_run_id"] == "1234567890"
    assert outputs["workflow_linux_validation_terminal_dispatch_execution_run_url"].endswith(
        "/actions/runs/1234567890"
    )
    assert outputs["workflow_linux_validation_terminal_dispatch_execution_command_returncode"] == ""
    assert outputs["workflow_linux_validation_terminal_dispatch_execution_report_json"].endswith(
        "ci_workflow_linux_validation_terminal_dispatch_execution.json"
    )
    assert outputs["workflow_linux_validation_terminal_dispatch_execution_report_markdown"].endswith(
        "ci_workflow_linux_validation_terminal_dispatch_execution.md"
    )

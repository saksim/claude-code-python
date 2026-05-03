"""Contract tests for P2-64 Linux CI workflow Linux validation final verdict gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_linux_validation_final_verdict_gate_module():
    script_path = (
        Path("scripts") / "run_p2_lv_final_verdict_gate.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_linux_validation_final_verdict_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_linux_validation_terminal_publish_payload() -> dict:
    return {
        "generated_at": "2026-05-02T00:00:00+00:00",
        "source_linux_validation_verdict_publish_report": "/tmp/ci_workflow_linux_validation_verdict_publish.json",
        "source_linux_validation_verdict_report": "/tmp/ci_workflow_linux_validation_verdict.json",
        "source_linux_validation_dispatch_report": "/tmp/ci_workflow_linux_validation_dispatch.json",
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
        "linux_validation_verdict_status": "validated",
        "linux_validation_verdict_decision": "accept_linux_validation",
        "linux_validation_verdict_exit_code": 0,
        "linux_validation_passed": True,
        "linux_validation_verdict_requires_manual_action": False,
        "linux_validation_verdict_channel": "release",
        "linux_validation_verdict_attempted": False,
        "linux_validation_verdict_timeout_seconds": 900,
        "linux_validation_verdict_command": "",
        "linux_validation_verdict_command_parts": [],
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
        "linux_validation_verdict_summary": (
            "linux_validation_dispatch_status=ready_dry_run "
            "linux_validation_dispatch_decision=dispatch_linux_validation "
            "linux_validation_verdict_status=validated "
            "linux_validation_verdict_decision=accept_linux_validation"
        ),
        "linux_validation_verdict_publish_status": "published",
        "linux_validation_verdict_publish_decision": "announce_linux_validation_passed",
        "linux_validation_verdict_publish_exit_code": 0,
        "linux_validation_verdict_publish_should_notify": True,
        "linux_validation_verdict_publish_requires_manual_action": False,
        "linux_validation_verdict_publish_channel": "release",
        "linux_validation_verdict_publish_summary": (
            "linux_validation_verdict_status=validated "
            "linux_validation_verdict_publish_status=published "
            "linux_validation_verdict_publish_decision=announce_linux_validation_passed"
        ),
        "linux_validation_terminal_publish_status": "terminal_published",
        "linux_validation_terminal_publish_decision": "announce_linux_validation_terminal_passed",
        "linux_validation_terminal_publish_exit_code": 0,
        "linux_validation_terminal_publish_should_notify": True,
        "linux_validation_terminal_publish_ready_for_handoff": True,
        "linux_validation_terminal_publish_requires_manual_action": False,
        "linux_validation_terminal_publish_channel": "release",
        "linux_validation_terminal_publish_summary": (
            "linux_validation_verdict_publish_status=published "
            "linux_validation_terminal_publish_status=terminal_published "
            "linux_validation_terminal_publish_decision=announce_linux_validation_terminal_passed"
        ),
        "reason_codes": ["linux_validation_terminal_publish_terminal_published"],
        "structural_issues": [],
        "missing_artifacts": [],
        "evidence_manifest": [
            {
                "source": "dispatch",
                "path": "/tmp/ci_workflow_linux_validation_dispatch.json",
                "exists": True,
            },
            {
                "source": "verdict",
                "path": "/tmp/ci_workflow_linux_validation_verdict.json",
                "exists": True,
            },
            {
                "source": "terminal_publish",
                "path": "/tmp/ci_workflow_linux_validation_terminal_publish.json",
                "exists": True,
            },
        ],
    }


def test_build_linux_validation_final_verdict_payload_validated(tmp_path: Path):
    gate = _load_ci_workflow_linux_validation_final_verdict_gate_module()
    terminal_payload = _sample_linux_validation_terminal_publish_payload()

    report_path = tmp_path / "ci_workflow_linux_validation_terminal_publish.json"
    report_path.write_text(json.dumps(terminal_payload, indent=2), encoding="utf-8")

    report = gate.load_linux_validation_terminal_publish_report(report_path)
    final_payload = gate.build_linux_validation_final_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert final_payload["linux_validation_final_verdict_status"] == "validated"
    assert (
        final_payload["linux_validation_final_verdict_decision"]
        == "accept_linux_validation_terminal"
    )
    assert final_payload["linux_validation_final_verdict_exit_code"] == 0
    assert final_payload["linux_validation_final_should_accept"] is True
    assert final_payload["linux_validation_final_requires_follow_up"] is False
    assert final_payload["linux_validation_final_should_page_owner"] is False
    assert final_payload["linux_validation_final_channel"] == "release"
    assert final_payload["reason_codes"] == ["linux_validation_final_verdict_validated"]


def test_build_linux_validation_final_verdict_payload_validated_with_follow_up(
    tmp_path: Path,
):
    gate = _load_ci_workflow_linux_validation_final_verdict_gate_module()
    terminal_payload = _sample_linux_validation_terminal_publish_payload()
    terminal_payload["terminal_verdict_status"] = "ready_with_follow_up_for_linux_validation"
    terminal_payload["terminal_verdict_decision"] = "proceed_linux_validation_with_follow_up"
    terminal_payload["terminal_verdict_exit_code"] = 1
    terminal_payload["terminal_verdict_channel"] = "follow_up"
    terminal_payload["linux_validation_channel"] = "follow_up"
    terminal_payload["linux_validation_dispatch_status"] = "ready_with_follow_up_dry_run"
    terminal_payload["linux_validation_dispatch_decision"] = (
        "dispatch_linux_validation_with_follow_up"
    )
    terminal_payload["linux_validation_dispatch_exit_code"] = 1
    terminal_payload["linux_validation_verdict_status"] = "validated_with_follow_up"
    terminal_payload["linux_validation_verdict_decision"] = (
        "accept_linux_validation_with_follow_up"
    )
    terminal_payload["linux_validation_verdict_exit_code"] = 1
    terminal_payload["linux_validation_verdict_channel"] = "follow_up"
    terminal_payload["linux_validation_verdict_publish_status"] = "published_with_follow_up"
    terminal_payload["linux_validation_verdict_publish_decision"] = (
        "announce_linux_validation_passed_with_follow_up"
    )
    terminal_payload["linux_validation_verdict_publish_exit_code"] = 1
    terminal_payload["linux_validation_verdict_publish_channel"] = "follow_up"
    terminal_payload["linux_validation_terminal_publish_status"] = (
        "terminal_published_with_follow_up"
    )
    terminal_payload["linux_validation_terminal_publish_decision"] = (
        "announce_linux_validation_terminal_passed_with_follow_up"
    )
    terminal_payload["linux_validation_terminal_publish_exit_code"] = 1
    terminal_payload["linux_validation_terminal_publish_ready_for_handoff"] = True
    terminal_payload["linux_validation_terminal_publish_requires_manual_action"] = False
    terminal_payload["linux_validation_terminal_publish_channel"] = "follow_up"
    terminal_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    terminal_payload["reason_codes"] = [
        "linux_validation_terminal_publish_terminal_published_with_follow_up"
    ]

    report_path = tmp_path / "ci_workflow_linux_validation_terminal_publish_follow_up.json"
    report_path.write_text(json.dumps(terminal_payload, indent=2), encoding="utf-8")

    report = gate.load_linux_validation_terminal_publish_report(report_path)
    final_payload = gate.build_linux_validation_final_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert (
        final_payload["linux_validation_final_verdict_status"]
        == "validated_with_follow_up"
    )
    assert (
        final_payload["linux_validation_final_verdict_decision"]
        == "accept_linux_validation_terminal_with_follow_up"
    )
    assert final_payload["linux_validation_final_verdict_exit_code"] == 1
    assert final_payload["linux_validation_final_should_accept"] is True
    assert final_payload["linux_validation_final_requires_follow_up"] is True
    assert final_payload["linux_validation_final_should_page_owner"] is False
    assert final_payload["linux_validation_final_channel"] == "follow_up"
    assert "linux_validation_final_verdict_validated_with_follow_up" in final_payload["reason_codes"]
    assert final_payload["follow_up_queue_url"].endswith("/issues/77")


def test_build_linux_validation_final_verdict_payload_blocked(tmp_path: Path):
    gate = _load_ci_workflow_linux_validation_final_verdict_gate_module()
    terminal_payload = _sample_linux_validation_terminal_publish_payload()
    terminal_payload["terminal_verdict_status"] = "blocked"
    terminal_payload["terminal_verdict_decision"] = "halt_linux_validation_blocker"
    terminal_payload["terminal_verdict_exit_code"] = 1
    terminal_payload["terminal_verdict_should_proceed"] = False
    terminal_payload["terminal_verdict_requires_manual_action"] = True
    terminal_payload["terminal_verdict_channel"] = "blocker"
    terminal_payload["linux_validation_should_dispatch"] = False
    terminal_payload["linux_validation_requires_manual_action"] = True
    terminal_payload["linux_validation_channel"] = "blocker"
    terminal_payload["linux_validation_dispatch_status"] = "blocked"
    terminal_payload["linux_validation_dispatch_decision"] = "hold_linux_validation_blocker"
    terminal_payload["linux_validation_dispatch_exit_code"] = 1
    terminal_payload["linux_validation_verdict_status"] = "blocked"
    terminal_payload["linux_validation_verdict_decision"] = "hold_linux_validation_blocker"
    terminal_payload["linux_validation_verdict_exit_code"] = 1
    terminal_payload["linux_validation_passed"] = False
    terminal_payload["linux_validation_verdict_requires_manual_action"] = True
    terminal_payload["linux_validation_verdict_channel"] = "blocker"
    terminal_payload["linux_validation_verdict_publish_status"] = "blocked"
    terminal_payload["linux_validation_verdict_publish_decision"] = (
        "announce_linux_validation_blocker"
    )
    terminal_payload["linux_validation_verdict_publish_exit_code"] = 1
    terminal_payload["linux_validation_verdict_publish_requires_manual_action"] = True
    terminal_payload["linux_validation_verdict_publish_channel"] = "blocker"
    terminal_payload["linux_validation_terminal_publish_status"] = "terminal_blocked"
    terminal_payload["linux_validation_terminal_publish_decision"] = (
        "announce_linux_validation_terminal_blocker"
    )
    terminal_payload["linux_validation_terminal_publish_exit_code"] = 1
    terminal_payload["linux_validation_terminal_publish_ready_for_handoff"] = False
    terminal_payload["linux_validation_terminal_publish_requires_manual_action"] = True
    terminal_payload["linux_validation_terminal_publish_channel"] = "blocker"
    terminal_payload["reason_codes"] = ["linux_validation_terminal_publish_terminal_blocked"]

    report_path = tmp_path / "ci_workflow_linux_validation_terminal_publish_blocked.json"
    report_path.write_text(json.dumps(terminal_payload, indent=2), encoding="utf-8")

    report = gate.load_linux_validation_terminal_publish_report(report_path)
    final_payload = gate.build_linux_validation_final_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert final_payload["linux_validation_final_verdict_status"] == "blocked"
    assert (
        final_payload["linux_validation_final_verdict_decision"]
        == "escalate_linux_validation_terminal_blocker"
    )
    assert final_payload["linux_validation_final_verdict_exit_code"] == 1
    assert final_payload["linux_validation_final_should_accept"] is False
    assert final_payload["linux_validation_final_requires_follow_up"] is True
    assert final_payload["linux_validation_final_should_page_owner"] is True
    assert final_payload["linux_validation_final_channel"] == "blocker"
    assert "linux_validation_final_verdict_blocked" in final_payload["reason_codes"]


def test_build_linux_validation_final_verdict_payload_rejects_contract_mismatch(
    tmp_path: Path,
):
    gate = _load_ci_workflow_linux_validation_final_verdict_gate_module()
    terminal_payload = _sample_linux_validation_terminal_publish_payload()
    terminal_payload["linux_validation_terminal_publish_status"] = "terminal_published"
    terminal_payload["linux_validation_terminal_publish_decision"] = (
        "announce_linux_validation_terminal_passed_with_follow_up"
    )
    terminal_payload["linux_validation_terminal_publish_ready_for_handoff"] = False
    terminal_payload["linux_validation_terminal_publish_requires_manual_action"] = True
    terminal_payload["linux_validation_terminal_publish_channel"] = "follow_up"

    report_path = tmp_path / "ci_workflow_linux_validation_terminal_publish_mismatch.json"
    report_path.write_text(json.dumps(terminal_payload, indent=2), encoding="utf-8")

    report = gate.load_linux_validation_terminal_publish_report(report_path)
    final_payload = gate.build_linux_validation_final_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )

    assert final_payload["linux_validation_final_verdict_status"] == "contract_failed"
    assert (
        final_payload["linux_validation_final_verdict_decision"]
        == "abort_linux_validation_terminal_verdict"
    )
    assert final_payload["linux_validation_final_verdict_exit_code"] == 1
    assert (
        "linux_validation_terminal_publish_decision_mismatch"
        in final_payload["structural_issues"]
    )
    assert (
        "linux_validation_terminal_publish_ready_for_handoff_mismatch"
        in final_payload["structural_issues"]
    )
    assert (
        "linux_validation_terminal_publish_requires_manual_action_mismatch"
        in final_payload["structural_issues"]
    )
    assert (
        "linux_validation_terminal_publish_channel_mismatch"
        in final_payload["structural_issues"]
    )


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_linux_validation_final_verdict_gate_module()
    terminal_payload = _sample_linux_validation_terminal_publish_payload()
    terminal_payload["terminal_verdict_status"] = "ready_with_follow_up_for_linux_validation"
    terminal_payload["terminal_verdict_decision"] = "proceed_linux_validation_with_follow_up"
    terminal_payload["terminal_verdict_exit_code"] = 1
    terminal_payload["terminal_verdict_channel"] = "follow_up"
    terminal_payload["linux_validation_channel"] = "follow_up"
    terminal_payload["linux_validation_dispatch_status"] = "ready_with_follow_up_dry_run"
    terminal_payload["linux_validation_dispatch_decision"] = (
        "dispatch_linux_validation_with_follow_up"
    )
    terminal_payload["linux_validation_dispatch_exit_code"] = 1
    terminal_payload["linux_validation_verdict_status"] = "validated_with_follow_up"
    terminal_payload["linux_validation_verdict_decision"] = (
        "accept_linux_validation_with_follow_up"
    )
    terminal_payload["linux_validation_verdict_exit_code"] = 1
    terminal_payload["linux_validation_verdict_channel"] = "follow_up"
    terminal_payload["linux_validation_verdict_publish_status"] = "published_with_follow_up"
    terminal_payload["linux_validation_verdict_publish_decision"] = (
        "announce_linux_validation_passed_with_follow_up"
    )
    terminal_payload["linux_validation_verdict_publish_exit_code"] = 1
    terminal_payload["linux_validation_verdict_publish_channel"] = "follow_up"
    terminal_payload["linux_validation_terminal_publish_status"] = (
        "terminal_published_with_follow_up"
    )
    terminal_payload["linux_validation_terminal_publish_decision"] = (
        "announce_linux_validation_terminal_passed_with_follow_up"
    )
    terminal_payload["linux_validation_terminal_publish_exit_code"] = 1
    terminal_payload["linux_validation_terminal_publish_ready_for_handoff"] = True
    terminal_payload["linux_validation_terminal_publish_requires_manual_action"] = False
    terminal_payload["linux_validation_terminal_publish_channel"] = "follow_up"
    terminal_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    terminal_payload["reason_codes"] = [
        "linux_validation_terminal_publish_terminal_published_with_follow_up"
    ]

    report_path = tmp_path / "ci_workflow_linux_validation_terminal_publish_output.json"
    report_path.write_text(json.dumps(terminal_payload, indent=2), encoding="utf-8")

    report = gate.load_linux_validation_terminal_publish_report(report_path)
    final_payload = gate.build_linux_validation_final_verdict_payload(
        report,
        source_path=report_path.resolve(),
    )
    outputs = gate.build_github_output_values(
        final_payload,
        output_json=Path(".claude/reports/linux_unified_gate/ci_workflow_linux_validation_final_verdict.json"),
        output_markdown=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_linux_validation_final_verdict.md"
        ),
    )

    assert outputs["workflow_linux_validation_final_verdict_status"] == "validated_with_follow_up"
    assert (
        outputs["workflow_linux_validation_final_verdict_decision"]
        == "accept_linux_validation_terminal_with_follow_up"
    )
    assert outputs["workflow_linux_validation_final_verdict_exit_code"] == "1"
    assert outputs["workflow_linux_validation_final_should_accept"] == "true"
    assert outputs["workflow_linux_validation_final_requires_follow_up"] == "true"
    assert outputs["workflow_linux_validation_final_should_page_owner"] == "false"
    assert outputs["workflow_linux_validation_final_channel"] == "follow_up"
    assert (
        outputs["workflow_linux_validation_final_terminal_publish_status"]
        == "terminal_published_with_follow_up"
    )
    assert outputs["workflow_linux_validation_final_terminal_publish_channel"] == "follow_up"
    assert outputs["workflow_linux_validation_final_follow_up_queue_url"].endswith("/issues/77")
    assert outputs["workflow_linux_validation_final_run_id"] == "1234567890"
    assert outputs["workflow_linux_validation_final_run_url"].endswith(
        "/actions/runs/1234567890"
    )
    assert outputs["workflow_linux_validation_final_report_json"].endswith(
        "ci_workflow_linux_validation_final_verdict.json"
    )
    assert outputs["workflow_linux_validation_final_report_markdown"].endswith(
        "ci_workflow_linux_validation_final_verdict.md"
    )

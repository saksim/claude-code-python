"""Contract tests for P2-67 Linux CI workflow Linux validation terminal verdict gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_linux_validation_terminal_verdict_gate_module():
    script_path = (
        Path("scripts")
        / "run_p2_lv_terminal_verdict_gate.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_linux_validation_terminal_verdict_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_linux_validation_final_publish_archive_payload() -> dict:
    return {
        "generated_at": "2026-05-02T00:00:00+00:00",
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
        "linux_validation_final_publish_archive_status": "archived",
        "linux_validation_final_publish_archive_decision": "archive_release_shipped",
        "linux_validation_final_publish_archive_exit_code": 0,
        "linux_validation_final_publish_archive_should_archive": True,
        "linux_validation_final_publish_archive_requires_manual_action": False,
        "linux_validation_final_publish_archive_channel": "release",
        "linux_validation_final_publish_archive_attempted": False,
        "linux_validation_final_publish_archive_timeout_seconds": 900,
        "linux_validation_final_publish_archive_command": "",
        "linux_validation_final_publish_archive_command_parts": [],
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
        "linux_validation_final_publish_archive_summary": (
            "linux_validation_final_verdict_publish_status=published "
            "linux_validation_final_publish_archive_status=archived "
            "linux_validation_final_publish_archive_decision=archive_release_shipped"
        ),
        "reason_codes": ["linux_validation_final_publish_archive_archived"],
        "structural_issues": [],
        "missing_artifacts": [],
        "evidence_manifest": [
            {
                "source": "dispatch",
                "path": "/tmp/ci_workflow_linux_validation_dispatch.json",
                "exists": True,
            },
            {
                "source": "final_publish_archive",
                "path": "/tmp/ci_workflow_linux_validation_final_publish_archive.json",
                "exists": True,
            },
        ],
    }


def test_build_linux_validation_terminal_verdict_payload_ready_for_linux_validation(
    tmp_path: Path,
):
    gate = _load_ci_workflow_linux_validation_terminal_verdict_gate_module()
    archive_payload = _sample_linux_validation_final_publish_archive_payload()

    archive_path = tmp_path / "ci_workflow_linux_validation_final_publish_archive.json"
    archive_path.write_text(json.dumps(archive_payload, indent=2), encoding="utf-8")

    archive_report = gate.load_linux_validation_final_publish_archive_report(archive_path)
    payload = gate.build_linux_validation_terminal_verdict_payload(
        archive_report,
        source_path=archive_path.resolve(),
    )

    assert payload["linux_validation_terminal_verdict_status"] == "ready_for_linux_validation"
    assert payload["linux_validation_terminal_verdict_decision"] == "proceed_linux_validation"
    assert payload["linux_validation_terminal_verdict_exit_code"] == 0
    assert payload["linux_validation_terminal_verdict_should_proceed"] is True
    assert payload["linux_validation_terminal_verdict_requires_manual_action"] is False
    assert payload["linux_validation_terminal_verdict_channel"] == "release"
    assert "linux_validation_terminal_verdict_ready_for_linux_validation" in payload["reason_codes"]


def test_build_linux_validation_terminal_verdict_payload_ready_with_follow_up(
    tmp_path: Path,
):
    gate = _load_ci_workflow_linux_validation_terminal_verdict_gate_module()
    archive_payload = _sample_linux_validation_final_publish_archive_payload()
    archive_payload["terminal_verdict_status"] = "ready_with_follow_up_for_linux_validation"
    archive_payload["terminal_verdict_decision"] = "proceed_linux_validation_with_follow_up"
    archive_payload["terminal_verdict_exit_code"] = 1
    archive_payload["terminal_verdict_channel"] = "follow_up"
    archive_payload["linux_validation_channel"] = "follow_up"
    archive_payload["linux_validation_dispatch_status"] = "ready_with_follow_up_dry_run"
    archive_payload["linux_validation_dispatch_decision"] = (
        "dispatch_linux_validation_with_follow_up"
    )
    archive_payload["linux_validation_dispatch_exit_code"] = 1
    archive_payload["linux_validation_final_publish_archive_status"] = "archived_with_follow_up"
    archive_payload["linux_validation_final_publish_archive_decision"] = (
        "archive_release_shipped_with_follow_up"
    )
    archive_payload["linux_validation_final_publish_archive_exit_code"] = 1
    archive_payload["linux_validation_final_publish_archive_requires_manual_action"] = False
    archive_payload["linux_validation_final_publish_archive_channel"] = "follow_up"
    archive_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    archive_payload["reason_codes"] = [
        "linux_validation_final_publish_archive_archived_with_follow_up"
    ]

    archive_path = tmp_path / "ci_workflow_linux_validation_final_publish_archive_follow_up.json"
    archive_path.write_text(json.dumps(archive_payload, indent=2), encoding="utf-8")

    archive_report = gate.load_linux_validation_final_publish_archive_report(archive_path)
    payload = gate.build_linux_validation_terminal_verdict_payload(
        archive_report,
        source_path=archive_path.resolve(),
    )

    assert payload["linux_validation_terminal_verdict_status"] == "ready_with_follow_up_for_linux_validation"
    assert payload["linux_validation_terminal_verdict_decision"] == "proceed_linux_validation_with_follow_up"
    assert payload["linux_validation_terminal_verdict_exit_code"] == 1
    assert payload["linux_validation_terminal_verdict_should_proceed"] is True
    assert payload["linux_validation_terminal_verdict_requires_manual_action"] is False
    assert payload["linux_validation_terminal_verdict_channel"] == "follow_up"
    assert (
        "linux_validation_terminal_verdict_ready_with_follow_up_for_linux_validation"
        in payload["reason_codes"]
    )
    assert payload["follow_up_queue_url"].endswith("/issues/77")


def test_build_linux_validation_terminal_verdict_payload_blocked(tmp_path: Path):
    gate = _load_ci_workflow_linux_validation_terminal_verdict_gate_module()
    archive_payload = _sample_linux_validation_final_publish_archive_payload()
    archive_payload["terminal_verdict_status"] = "blocked"
    archive_payload["terminal_verdict_decision"] = "halt_linux_validation_blocker"
    archive_payload["terminal_verdict_exit_code"] = 1
    archive_payload["terminal_verdict_should_proceed"] = False
    archive_payload["terminal_verdict_requires_manual_action"] = True
    archive_payload["terminal_verdict_channel"] = "blocker"
    archive_payload["linux_validation_should_dispatch"] = False
    archive_payload["linux_validation_requires_manual_action"] = True
    archive_payload["linux_validation_channel"] = "blocker"
    archive_payload["linux_validation_dispatch_status"] = "blocked"
    archive_payload["linux_validation_dispatch_decision"] = "hold_linux_validation_blocker"
    archive_payload["linux_validation_dispatch_exit_code"] = 1
    archive_payload["linux_validation_final_publish_archive_status"] = "blocked"
    archive_payload["linux_validation_final_publish_archive_decision"] = "archive_release_blocker"
    archive_payload["linux_validation_final_publish_archive_exit_code"] = 1
    archive_payload["linux_validation_final_publish_archive_should_archive"] = False
    archive_payload["linux_validation_final_publish_archive_requires_manual_action"] = True
    archive_payload["linux_validation_final_publish_archive_channel"] = "blocker"
    archive_payload["reason_codes"] = ["linux_validation_final_publish_archive_blocked"]

    archive_path = tmp_path / "ci_workflow_linux_validation_final_publish_archive_blocked.json"
    archive_path.write_text(json.dumps(archive_payload, indent=2), encoding="utf-8")

    archive_report = gate.load_linux_validation_final_publish_archive_report(archive_path)
    payload = gate.build_linux_validation_terminal_verdict_payload(
        archive_report,
        source_path=archive_path.resolve(),
    )

    assert payload["linux_validation_terminal_verdict_status"] == "blocked"
    assert payload["linux_validation_terminal_verdict_decision"] == "halt_linux_validation_blocker"
    assert payload["linux_validation_terminal_verdict_exit_code"] == 1
    assert payload["linux_validation_terminal_verdict_should_proceed"] is False
    assert payload["linux_validation_terminal_verdict_requires_manual_action"] is True
    assert payload["linux_validation_terminal_verdict_channel"] == "blocker"
    assert "linux_validation_terminal_verdict_blocked" in payload["reason_codes"]


def test_build_linux_validation_terminal_verdict_payload_rejects_contract_mismatch(
    tmp_path: Path,
):
    gate = _load_ci_workflow_linux_validation_terminal_verdict_gate_module()
    archive_payload = _sample_linux_validation_final_publish_archive_payload()
    archive_payload["linux_validation_final_publish_archive_status"] = "archived"
    archive_payload["linux_validation_final_publish_archive_decision"] = (
        "archive_release_shipped_with_follow_up"
    )
    archive_payload["linux_validation_final_publish_archive_requires_manual_action"] = False
    archive_payload["linux_validation_final_publish_archive_channel"] = "follow_up"

    archive_path = tmp_path / "ci_workflow_linux_validation_final_publish_archive_mismatch.json"
    archive_path.write_text(json.dumps(archive_payload, indent=2), encoding="utf-8")

    archive_report = gate.load_linux_validation_final_publish_archive_report(archive_path)
    payload = gate.build_linux_validation_terminal_verdict_payload(
        archive_report,
        source_path=archive_path.resolve(),
    )

    assert payload["linux_validation_terminal_verdict_status"] == "contract_failed"
    assert payload["linux_validation_terminal_verdict_decision"] == "abort_linux_validation"
    assert payload["linux_validation_terminal_verdict_exit_code"] == 1
    assert "linux_validation_final_publish_archive_decision_mismatch" in payload["structural_issues"]
    assert "linux_validation_final_publish_archive_requires_manual_action_mismatch" in payload["structural_issues"]
    assert "linux_validation_final_publish_archive_channel_mismatch" in payload["structural_issues"]


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_linux_validation_terminal_verdict_gate_module()
    archive_payload = _sample_linux_validation_final_publish_archive_payload()
    archive_payload["terminal_verdict_status"] = "ready_with_follow_up_for_linux_validation"
    archive_payload["terminal_verdict_decision"] = "proceed_linux_validation_with_follow_up"
    archive_payload["terminal_verdict_exit_code"] = 1
    archive_payload["terminal_verdict_channel"] = "follow_up"
    archive_payload["linux_validation_channel"] = "follow_up"
    archive_payload["linux_validation_dispatch_status"] = "ready_with_follow_up_dry_run"
    archive_payload["linux_validation_dispatch_decision"] = (
        "dispatch_linux_validation_with_follow_up"
    )
    archive_payload["linux_validation_dispatch_exit_code"] = 1
    archive_payload["linux_validation_final_publish_archive_status"] = "archived_with_follow_up"
    archive_payload["linux_validation_final_publish_archive_decision"] = (
        "archive_release_shipped_with_follow_up"
    )
    archive_payload["linux_validation_final_publish_archive_exit_code"] = 1
    archive_payload["linux_validation_final_publish_archive_requires_manual_action"] = False
    archive_payload["linux_validation_final_publish_archive_channel"] = "follow_up"
    archive_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    archive_payload["reason_codes"] = [
        "linux_validation_final_publish_archive_archived_with_follow_up"
    ]

    archive_path = tmp_path / "ci_workflow_linux_validation_final_publish_archive_output.json"
    archive_path.write_text(json.dumps(archive_payload, indent=2), encoding="utf-8")

    archive_report = gate.load_linux_validation_final_publish_archive_report(archive_path)
    payload = gate.build_linux_validation_terminal_verdict_payload(
        archive_report,
        source_path=archive_path.resolve(),
    )
    outputs = gate.build_github_output_values(
        payload,
        output_json=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_verdict.json"
        ),
        output_markdown=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_verdict.md"
        ),
    )

    assert outputs["workflow_linux_validation_terminal_verdict_status"] == "ready_with_follow_up_for_linux_validation"
    assert outputs["workflow_linux_validation_terminal_verdict_decision"] == "proceed_linux_validation_with_follow_up"
    assert outputs["workflow_linux_validation_terminal_verdict_exit_code"] == "1"
    assert outputs["workflow_linux_validation_terminal_verdict_should_proceed"] == "true"
    assert outputs["workflow_linux_validation_terminal_verdict_requires_manual_action"] == "false"
    assert outputs["workflow_linux_validation_terminal_verdict_channel"] == "follow_up"
    assert outputs["workflow_linux_validation_terminal_verdict_follow_up_queue_url"].endswith(
        "/issues/77"
    )
    assert outputs["workflow_linux_validation_terminal_verdict_run_id"] == "1234567890"
    assert outputs["workflow_linux_validation_terminal_verdict_run_url"].endswith(
        "/actions/runs/1234567890"
    )
    assert outputs["workflow_linux_validation_terminal_verdict_report_json"].endswith(
        "ci_workflow_linux_validation_terminal_verdict.json"
    )
    assert outputs["workflow_linux_validation_terminal_verdict_report_markdown"].endswith(
        "ci_workflow_linux_validation_terminal_verdict.md"
    )

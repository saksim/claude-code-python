"""Contract tests for P2-66 Linux CI workflow Linux validation final publish archive gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_linux_validation_final_publish_archive_gate_module():
    script_path = (
        Path("scripts")
        / "run_p2_lv_final_publish_archive_gate.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_linux_validation_final_publish_archive_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_linux_validation_final_verdict_publish_payload() -> dict:
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
        "linux_validation_final_verdict_publish_status": "published",
        "linux_validation_final_verdict_publish_decision": "announce_linux_validation_final_validated",
        "linux_validation_final_verdict_publish_exit_code": 0,
        "linux_validation_final_verdict_publish_should_notify": True,
        "linux_validation_final_verdict_publish_requires_manual_action": False,
        "linux_validation_final_verdict_publish_channel": "release",
        "linux_validation_final_verdict_publish_attempted": False,
        "linux_validation_final_verdict_publish_timeout_seconds": 900,
        "linux_validation_final_verdict_publish_command": "",
        "linux_validation_final_verdict_publish_command_parts": [],
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
        "linux_validation_final_verdict_publish_summary": (
            "linux_validation_terminal_publish_status=terminal_published "
            "linux_validation_final_verdict_publish_status=published "
            "linux_validation_final_verdict_publish_decision=announce_linux_validation_final_validated"
        ),
        "reason_codes": ["linux_validation_final_verdict_publish_published"],
        "structural_issues": [],
        "missing_artifacts": [],
        "evidence_manifest": [
            {
                "source": "dispatch",
                "path": "/tmp/ci_workflow_linux_validation_dispatch.json",
                "exists": True,
            },
            {
                "source": "final_verdict_publish",
                "path": "/tmp/ci_workflow_linux_validation_final_verdict_publish.json",
                "exists": True,
            },
        ],
    }


def test_build_linux_validation_final_publish_archive_payload_published(tmp_path: Path):
    gate = _load_ci_workflow_linux_validation_final_publish_archive_gate_module()
    final_verdict_payload = _sample_linux_validation_final_verdict_publish_payload()

    final_verdict_path = tmp_path / "ci_workflow_linux_validation_final_verdict_publish.json"
    final_verdict_path.write_text(json.dumps(final_verdict_payload, indent=2), encoding="utf-8")

    final_verdict_report = gate.load_linux_validation_final_verdict_publish_report(final_verdict_path)
    publish_payload = gate.build_linux_validation_final_publish_archive_payload(
        final_verdict_report,
        source_path=final_verdict_path.resolve(),
    )

    assert publish_payload["linux_validation_final_publish_archive_status"] == "archived"
    assert (
        publish_payload["linux_validation_final_publish_archive_decision"]
        == "archive_release_shipped"
    )
    assert publish_payload["linux_validation_final_publish_archive_exit_code"] == 0
    assert publish_payload["linux_validation_final_publish_archive_should_archive"] is True
    assert (
        publish_payload["linux_validation_final_publish_archive_requires_manual_action"]
        is False
    )
    assert publish_payload["linux_validation_final_publish_archive_channel"] == "release"
    assert "linux_validation_final_publish_archive_archived" in publish_payload["reason_codes"]


def test_build_linux_validation_final_publish_archive_payload_published_with_follow_up(
    tmp_path: Path,
):
    gate = _load_ci_workflow_linux_validation_final_publish_archive_gate_module()
    final_verdict_payload = _sample_linux_validation_final_verdict_publish_payload()
    final_verdict_payload["terminal_verdict_status"] = "ready_with_follow_up_for_linux_validation"
    final_verdict_payload["terminal_verdict_decision"] = "proceed_linux_validation_with_follow_up"
    final_verdict_payload["terminal_verdict_exit_code"] = 1
    final_verdict_payload["terminal_verdict_channel"] = "follow_up"
    final_verdict_payload["linux_validation_channel"] = "follow_up"
    final_verdict_payload["linux_validation_dispatch_status"] = "ready_with_follow_up_dry_run"
    final_verdict_payload["linux_validation_dispatch_decision"] = (
        "dispatch_linux_validation_with_follow_up"
    )
    final_verdict_payload["linux_validation_dispatch_exit_code"] = 1
    final_verdict_payload["linux_validation_final_verdict_publish_status"] = "published_with_follow_up"
    final_verdict_payload["linux_validation_final_verdict_publish_decision"] = (
        "announce_linux_validation_final_validated_with_follow_up"
    )
    final_verdict_payload["linux_validation_final_verdict_publish_exit_code"] = 1
    final_verdict_payload["linux_validation_final_verdict_publish_requires_manual_action"] = True
    final_verdict_payload["linux_validation_final_verdict_publish_channel"] = "follow_up"
    final_verdict_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    final_verdict_payload["reason_codes"] = [
        "linux_validation_final_verdict_publish_published_with_follow_up"
    ]

    final_verdict_path = tmp_path / "ci_workflow_linux_validation_final_verdict_publish_follow_up.json"
    final_verdict_path.write_text(json.dumps(final_verdict_payload, indent=2), encoding="utf-8")

    final_verdict_report = gate.load_linux_validation_final_verdict_publish_report(final_verdict_path)
    publish_payload = gate.build_linux_validation_final_publish_archive_payload(
        final_verdict_report,
        source_path=final_verdict_path.resolve(),
    )

    assert (
        publish_payload["linux_validation_final_publish_archive_status"]
        == "archived_with_follow_up"
    )
    assert (
        publish_payload["linux_validation_final_publish_archive_decision"]
        == "archive_release_shipped_with_follow_up"
    )
    assert publish_payload["linux_validation_final_publish_archive_exit_code"] == 1
    assert publish_payload["linux_validation_final_publish_archive_should_archive"] is True
    assert (
        publish_payload["linux_validation_final_publish_archive_requires_manual_action"]
        is False
    )
    assert publish_payload["linux_validation_final_publish_archive_channel"] == "follow_up"
    assert "linux_validation_final_publish_archive_archived_with_follow_up" in publish_payload["reason_codes"]
    assert publish_payload["follow_up_queue_url"].endswith("/issues/77")


def test_build_linux_validation_final_publish_archive_payload_blocked(tmp_path: Path):
    gate = _load_ci_workflow_linux_validation_final_publish_archive_gate_module()
    final_verdict_payload = _sample_linux_validation_final_verdict_publish_payload()
    final_verdict_payload["terminal_verdict_status"] = "blocked"
    final_verdict_payload["terminal_verdict_decision"] = "halt_linux_validation_blocker"
    final_verdict_payload["terminal_verdict_exit_code"] = 1
    final_verdict_payload["terminal_verdict_should_proceed"] = False
    final_verdict_payload["terminal_verdict_requires_manual_action"] = True
    final_verdict_payload["terminal_verdict_channel"] = "blocker"
    final_verdict_payload["linux_validation_should_dispatch"] = False
    final_verdict_payload["linux_validation_requires_manual_action"] = True
    final_verdict_payload["linux_validation_channel"] = "blocker"
    final_verdict_payload["linux_validation_dispatch_status"] = "blocked"
    final_verdict_payload["linux_validation_dispatch_decision"] = "hold_linux_validation_blocker"
    final_verdict_payload["linux_validation_dispatch_exit_code"] = 1
    final_verdict_payload["linux_validation_final_verdict_publish_status"] = "blocked"
    final_verdict_payload["linux_validation_final_verdict_publish_decision"] = (
        "announce_linux_validation_final_blocker"
    )
    final_verdict_payload["linux_validation_final_verdict_publish_exit_code"] = 1
    final_verdict_payload["linux_validation_final_verdict_publish_should_notify"] = True
    final_verdict_payload["linux_validation_final_verdict_publish_requires_manual_action"] = True
    final_verdict_payload["linux_validation_final_verdict_publish_channel"] = "blocker"
    final_verdict_payload["reason_codes"] = ["linux_validation_final_verdict_publish_blocked"]

    final_verdict_path = tmp_path / "ci_workflow_linux_validation_final_verdict_publish_blocked.json"
    final_verdict_path.write_text(json.dumps(final_verdict_payload, indent=2), encoding="utf-8")

    final_verdict_report = gate.load_linux_validation_final_verdict_publish_report(final_verdict_path)
    publish_payload = gate.build_linux_validation_final_publish_archive_payload(
        final_verdict_report,
        source_path=final_verdict_path.resolve(),
    )

    assert publish_payload["linux_validation_final_publish_archive_status"] == "blocked"
    assert (
        publish_payload["linux_validation_final_publish_archive_decision"]
        == "archive_release_blocker"
    )
    assert publish_payload["linux_validation_final_publish_archive_exit_code"] == 1
    assert publish_payload["linux_validation_final_publish_archive_should_archive"] is False
    assert (
        publish_payload["linux_validation_final_publish_archive_requires_manual_action"]
        is True
    )
    assert publish_payload["linux_validation_final_publish_archive_channel"] == "blocker"
    assert "linux_validation_final_publish_archive_blocked" in publish_payload["reason_codes"]


def test_build_linux_validation_final_publish_archive_payload_rejects_contract_mismatch(
    tmp_path: Path,
):
    gate = _load_ci_workflow_linux_validation_final_publish_archive_gate_module()
    final_verdict_payload = _sample_linux_validation_final_verdict_publish_payload()
    final_verdict_payload["linux_validation_final_verdict_publish_status"] = "published"
    final_verdict_payload["linux_validation_final_verdict_publish_decision"] = (
        "announce_linux_validation_final_validated_with_follow_up"
    )
    final_verdict_payload["linux_validation_final_verdict_publish_requires_manual_action"] = False
    final_verdict_payload["linux_validation_final_verdict_publish_channel"] = "follow_up"

    final_verdict_path = tmp_path / "ci_workflow_linux_validation_final_verdict_publish_mismatch.json"
    final_verdict_path.write_text(json.dumps(final_verdict_payload, indent=2), encoding="utf-8")

    final_verdict_report = gate.load_linux_validation_final_verdict_publish_report(final_verdict_path)
    publish_payload = gate.build_linux_validation_final_publish_archive_payload(
        final_verdict_report,
        source_path=final_verdict_path.resolve(),
    )

    assert publish_payload["linux_validation_final_publish_archive_status"] == "contract_failed"
    assert publish_payload["linux_validation_final_publish_archive_decision"] == "abort_archive"
    assert publish_payload["linux_validation_final_publish_archive_exit_code"] == 1
    assert "linux_validation_final_publish_decision_mismatch" in publish_payload["structural_issues"]
    assert "linux_validation_final_publish_requires_manual_action_mismatch" in publish_payload["structural_issues"]
    assert "linux_validation_final_publish_channel_mismatch" in publish_payload["structural_issues"]


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_linux_validation_final_publish_archive_gate_module()
    final_verdict_payload = _sample_linux_validation_final_verdict_publish_payload()
    final_verdict_payload["terminal_verdict_status"] = "ready_with_follow_up_for_linux_validation"
    final_verdict_payload["terminal_verdict_decision"] = "proceed_linux_validation_with_follow_up"
    final_verdict_payload["terminal_verdict_exit_code"] = 1
    final_verdict_payload["terminal_verdict_channel"] = "follow_up"
    final_verdict_payload["linux_validation_channel"] = "follow_up"
    final_verdict_payload["linux_validation_dispatch_status"] = "ready_with_follow_up_dry_run"
    final_verdict_payload["linux_validation_dispatch_decision"] = (
        "dispatch_linux_validation_with_follow_up"
    )
    final_verdict_payload["linux_validation_dispatch_exit_code"] = 1
    final_verdict_payload["linux_validation_final_verdict_publish_status"] = "published_with_follow_up"
    final_verdict_payload["linux_validation_final_verdict_publish_decision"] = (
        "announce_linux_validation_final_validated_with_follow_up"
    )
    final_verdict_payload["linux_validation_final_verdict_publish_exit_code"] = 1
    final_verdict_payload["linux_validation_final_verdict_publish_requires_manual_action"] = False
    final_verdict_payload["linux_validation_final_verdict_publish_channel"] = "follow_up"
    final_verdict_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    final_verdict_payload["reason_codes"] = [
        "linux_validation_final_verdict_publish_published_with_follow_up"
    ]

    final_verdict_path = tmp_path / "ci_workflow_linux_validation_final_verdict_publish_output.json"
    final_verdict_path.write_text(json.dumps(final_verdict_payload, indent=2), encoding="utf-8")

    final_verdict_report = gate.load_linux_validation_final_verdict_publish_report(final_verdict_path)
    publish_payload = gate.build_linux_validation_final_publish_archive_payload(
        final_verdict_report,
        source_path=final_verdict_path.resolve(),
    )
    outputs = gate.build_github_output_values(
        publish_payload,
        output_json=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_linux_validation_final_publish_archive.json"
        ),
        output_markdown=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_linux_validation_final_publish_archive.md"
        ),
    )

    assert outputs["workflow_linux_validation_final_publish_archive_status"] == "archived_with_follow_up"
    assert (
        outputs["workflow_linux_validation_final_publish_archive_decision"]
        == "archive_release_shipped_with_follow_up"
    )
    assert outputs["workflow_linux_validation_final_publish_archive_exit_code"] == "1"
    assert outputs["workflow_linux_validation_final_publish_archive_should_archive"] == "true"
    assert outputs["workflow_linux_validation_final_publish_archive_requires_manual_action"] == "false"
    assert outputs["workflow_linux_validation_final_publish_archive_channel"] == "follow_up"
    assert outputs["workflow_linux_validation_final_publish_archive_follow_up_queue_url"].endswith(
        "/issues/77"
    )
    assert outputs["workflow_linux_validation_final_publish_archive_run_id"] == "1234567890"
    assert outputs["workflow_linux_validation_final_publish_archive_run_url"].endswith(
        "/actions/runs/1234567890"
    )
    assert outputs["workflow_linux_validation_final_publish_archive_report_json"].endswith(
        "ci_workflow_linux_validation_final_publish_archive.json"
    )
    assert outputs["workflow_linux_validation_final_publish_archive_report_markdown"].endswith(
        "ci_workflow_linux_validation_final_publish_archive.md"
    )




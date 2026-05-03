"""Contract tests for P2-69 Linux CI workflow Linux validation terminal dispatch gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_linux_validation_terminal_dispatch_gate_module():
    script_path = (
        Path("scripts")
        / "run_p2_lv_td_dispatch_gate.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_linux_validation_terminal_dispatch_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_linux_validation_terminal_verdict_publish_payload() -> dict:
    return {
        "generated_at": "2026-05-02T00:00:00+00:00",
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
        "reason_codes": ["linux_validation_terminal_verdict_publish_published"],
        "structural_issues": [],
        "missing_artifacts": [],
        "evidence_manifest": [
            {
                "source": "dispatch",
                "path": "/tmp/ci_workflow_linux_validation_dispatch.json",
                "exists": True,
            },
            {
                "source": "terminal_verdict_publish",
                "path": "/tmp/ci_workflow_linux_validation_terminal_verdict_publish.json",
                "exists": True,
            },
        ],
    }


def test_build_linux_validation_terminal_dispatch_payload_ready_dry_run(tmp_path: Path):
    gate = _load_ci_workflow_linux_validation_terminal_dispatch_gate_module()
    terminal_publish_payload = _sample_linux_validation_terminal_verdict_publish_payload()

    publish_path = tmp_path / "ci_workflow_linux_validation_terminal_verdict_publish.json"
    publish_path.write_text(json.dumps(terminal_publish_payload, indent=2), encoding="utf-8")

    publish_report = gate.load_linux_validation_terminal_verdict_publish_report(publish_path)
    dispatch_payload = gate.build_linux_validation_terminal_dispatch_payload(
        publish_report,
        source_path=publish_path.resolve(),
    )

    assert dispatch_payload["linux_validation_terminal_dispatch_status"] == "ready_dry_run"
    assert (
        dispatch_payload["linux_validation_terminal_dispatch_decision"]
        == "dispatch_linux_validation_terminal"
    )
    assert dispatch_payload["linux_validation_terminal_dispatch_exit_code"] == 0
    assert dispatch_payload["linux_validation_terminal_should_dispatch"] is True
    assert dispatch_payload["linux_validation_terminal_dispatch_requires_manual_action"] is False
    assert dispatch_payload["linux_validation_terminal_dispatch_channel"] == "release"
    assert "linux_validation_terminal_dispatch_ready_dry_run" in dispatch_payload["reason_codes"]


def test_build_linux_validation_terminal_dispatch_payload_ready_with_follow_up_dry_run(
    tmp_path: Path,
):
    gate = _load_ci_workflow_linux_validation_terminal_dispatch_gate_module()
    terminal_publish_payload = _sample_linux_validation_terminal_verdict_publish_payload()
    terminal_publish_payload["terminal_verdict_status"] = "ready_with_follow_up_for_linux_validation"
    terminal_publish_payload["terminal_verdict_decision"] = "proceed_linux_validation_with_follow_up"
    terminal_publish_payload["terminal_verdict_exit_code"] = 1
    terminal_publish_payload["terminal_verdict_channel"] = "follow_up"
    terminal_publish_payload["linux_validation_channel"] = "follow_up"
    terminal_publish_payload["linux_validation_dispatch_status"] = "ready_with_follow_up_dry_run"
    terminal_publish_payload["linux_validation_dispatch_decision"] = (
        "dispatch_linux_validation_with_follow_up"
    )
    terminal_publish_payload["linux_validation_dispatch_exit_code"] = 1
    terminal_publish_payload["linux_validation_terminal_verdict_status"] = "ready_with_follow_up_for_linux_validation"
    terminal_publish_payload["linux_validation_terminal_verdict_decision"] = (
        "proceed_linux_validation_with_follow_up"
    )
    terminal_publish_payload["linux_validation_terminal_verdict_exit_code"] = 1
    terminal_publish_payload["linux_validation_terminal_verdict_requires_manual_action"] = False
    terminal_publish_payload["linux_validation_terminal_verdict_channel"] = "follow_up"
    terminal_publish_payload["linux_validation_terminal_verdict_publish_status"] = "published_with_follow_up"
    terminal_publish_payload["linux_validation_terminal_verdict_publish_decision"] = (
        "announce_linux_validation_terminal_ready_with_follow_up"
    )
    terminal_publish_payload["linux_validation_terminal_verdict_publish_exit_code"] = 1
    terminal_publish_payload["linux_validation_terminal_verdict_publish_requires_manual_action"] = False
    terminal_publish_payload["linux_validation_terminal_verdict_publish_channel"] = "follow_up"
    terminal_publish_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    terminal_publish_payload["reason_codes"] = [
        "linux_validation_terminal_verdict_publish_with_follow_up"
    ]

    publish_path = tmp_path / "ci_workflow_linux_validation_terminal_verdict_publish_follow_up.json"
    publish_path.write_text(json.dumps(terminal_publish_payload, indent=2), encoding="utf-8")

    publish_report = gate.load_linux_validation_terminal_verdict_publish_report(publish_path)
    dispatch_payload = gate.build_linux_validation_terminal_dispatch_payload(
        publish_report,
        source_path=publish_path.resolve(),
    )

    assert dispatch_payload["linux_validation_terminal_dispatch_status"] == "ready_with_follow_up_dry_run"
    assert (
        dispatch_payload["linux_validation_terminal_dispatch_decision"]
        == "dispatch_linux_validation_terminal_with_follow_up"
    )
    assert dispatch_payload["linux_validation_terminal_dispatch_exit_code"] == 1
    assert dispatch_payload["linux_validation_terminal_should_dispatch"] is True
    assert dispatch_payload["linux_validation_terminal_dispatch_requires_manual_action"] is False
    assert dispatch_payload["linux_validation_terminal_dispatch_channel"] == "follow_up"
    assert "linux_validation_terminal_dispatch_ready_with_follow_up_dry_run" in dispatch_payload["reason_codes"]
    assert dispatch_payload["follow_up_queue_url"].endswith("/issues/77")


def test_build_linux_validation_terminal_dispatch_payload_blocked(tmp_path: Path):
    gate = _load_ci_workflow_linux_validation_terminal_dispatch_gate_module()
    terminal_publish_payload = _sample_linux_validation_terminal_verdict_publish_payload()
    terminal_publish_payload["terminal_verdict_status"] = "blocked"
    terminal_publish_payload["terminal_verdict_decision"] = "halt_linux_validation_blocker"
    terminal_publish_payload["terminal_verdict_exit_code"] = 1
    terminal_publish_payload["terminal_verdict_should_proceed"] = False
    terminal_publish_payload["terminal_verdict_requires_manual_action"] = True
    terminal_publish_payload["terminal_verdict_channel"] = "blocker"
    terminal_publish_payload["linux_validation_should_dispatch"] = False
    terminal_publish_payload["linux_validation_requires_manual_action"] = True
    terminal_publish_payload["linux_validation_channel"] = "blocker"
    terminal_publish_payload["linux_validation_dispatch_status"] = "blocked"
    terminal_publish_payload["linux_validation_dispatch_decision"] = "hold_linux_validation_blocker"
    terminal_publish_payload["linux_validation_dispatch_exit_code"] = 1
    terminal_publish_payload["linux_validation_terminal_verdict_status"] = "blocked"
    terminal_publish_payload["linux_validation_terminal_verdict_decision"] = (
        "halt_linux_validation_blocker"
    )
    terminal_publish_payload["linux_validation_terminal_verdict_exit_code"] = 1
    terminal_publish_payload["linux_validation_terminal_verdict_should_proceed"] = False
    terminal_publish_payload["linux_validation_terminal_verdict_requires_manual_action"] = True
    terminal_publish_payload["linux_validation_terminal_verdict_channel"] = "blocker"
    terminal_publish_payload["linux_validation_terminal_verdict_publish_status"] = "blocked"
    terminal_publish_payload["linux_validation_terminal_verdict_publish_decision"] = (
        "announce_linux_validation_terminal_blocker"
    )
    terminal_publish_payload["linux_validation_terminal_verdict_publish_exit_code"] = 1
    terminal_publish_payload["linux_validation_terminal_verdict_publish_requires_manual_action"] = True
    terminal_publish_payload["linux_validation_terminal_verdict_publish_channel"] = "blocker"
    terminal_publish_payload["reason_codes"] = ["linux_validation_terminal_verdict_publish_blocked"]

    publish_path = tmp_path / "ci_workflow_linux_validation_terminal_verdict_publish_blocked.json"
    publish_path.write_text(json.dumps(terminal_publish_payload, indent=2), encoding="utf-8")

    publish_report = gate.load_linux_validation_terminal_verdict_publish_report(publish_path)
    dispatch_payload = gate.build_linux_validation_terminal_dispatch_payload(
        publish_report,
        source_path=publish_path.resolve(),
    )

    assert dispatch_payload["linux_validation_terminal_dispatch_status"] == "blocked"
    assert (
        dispatch_payload["linux_validation_terminal_dispatch_decision"]
        == "hold_linux_validation_terminal_blocker"
    )
    assert dispatch_payload["linux_validation_terminal_dispatch_exit_code"] == 1
    assert dispatch_payload["linux_validation_terminal_should_dispatch"] is False
    assert dispatch_payload["linux_validation_terminal_dispatch_requires_manual_action"] is True
    assert dispatch_payload["linux_validation_terminal_dispatch_channel"] == "blocker"
    assert "linux_validation_terminal_dispatch_blocked" in dispatch_payload["reason_codes"]


def test_build_linux_validation_terminal_dispatch_payload_rejects_contract_mismatch(
    tmp_path: Path,
):
    gate = _load_ci_workflow_linux_validation_terminal_dispatch_gate_module()
    terminal_publish_payload = _sample_linux_validation_terminal_verdict_publish_payload()
    terminal_publish_payload["linux_validation_terminal_verdict_publish_status"] = "published"
    terminal_publish_payload["linux_validation_terminal_verdict_publish_decision"] = (
        "announce_linux_validation_terminal_ready_with_follow_up"
    )
    terminal_publish_payload["linux_validation_terminal_verdict_publish_requires_manual_action"] = False
    terminal_publish_payload["linux_validation_terminal_verdict_publish_channel"] = "follow_up"

    publish_path = tmp_path / "ci_workflow_linux_validation_terminal_verdict_publish_mismatch.json"
    publish_path.write_text(json.dumps(terminal_publish_payload, indent=2), encoding="utf-8")

    publish_report = gate.load_linux_validation_terminal_verdict_publish_report(publish_path)
    dispatch_payload = gate.build_linux_validation_terminal_dispatch_payload(
        publish_report,
        source_path=publish_path.resolve(),
    )

    assert dispatch_payload["linux_validation_terminal_dispatch_status"] == "contract_failed"
    assert dispatch_payload["linux_validation_terminal_dispatch_decision"] == "abort_linux_validation_terminal_dispatch"
    assert dispatch_payload["linux_validation_terminal_dispatch_exit_code"] == 1
    assert "linux_validation_terminal_dispatch_upstream_decision_mismatch" in dispatch_payload["structural_issues"]
    assert (
        "linux_validation_terminal_dispatch_upstream_requires_manual_action_mismatch"
        in dispatch_payload["structural_issues"]
    )
    assert "linux_validation_terminal_dispatch_upstream_channel_mismatch" in dispatch_payload["structural_issues"]


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_linux_validation_terminal_dispatch_gate_module()
    terminal_publish_payload = _sample_linux_validation_terminal_verdict_publish_payload()
    terminal_publish_payload["terminal_verdict_status"] = "ready_with_follow_up_for_linux_validation"
    terminal_publish_payload["terminal_verdict_decision"] = "proceed_linux_validation_with_follow_up"
    terminal_publish_payload["terminal_verdict_exit_code"] = 1
    terminal_publish_payload["terminal_verdict_channel"] = "follow_up"
    terminal_publish_payload["linux_validation_channel"] = "follow_up"
    terminal_publish_payload["linux_validation_dispatch_status"] = "ready_with_follow_up_dry_run"
    terminal_publish_payload["linux_validation_dispatch_decision"] = (
        "dispatch_linux_validation_with_follow_up"
    )
    terminal_publish_payload["linux_validation_dispatch_exit_code"] = 1
    terminal_publish_payload["linux_validation_terminal_verdict_status"] = "ready_with_follow_up_for_linux_validation"
    terminal_publish_payload["linux_validation_terminal_verdict_decision"] = (
        "proceed_linux_validation_with_follow_up"
    )
    terminal_publish_payload["linux_validation_terminal_verdict_exit_code"] = 1
    terminal_publish_payload["linux_validation_terminal_verdict_requires_manual_action"] = False
    terminal_publish_payload["linux_validation_terminal_verdict_channel"] = "follow_up"
    terminal_publish_payload["linux_validation_terminal_verdict_publish_status"] = "published_with_follow_up"
    terminal_publish_payload["linux_validation_terminal_verdict_publish_decision"] = (
        "announce_linux_validation_terminal_ready_with_follow_up"
    )
    terminal_publish_payload["linux_validation_terminal_verdict_publish_exit_code"] = 1
    terminal_publish_payload["linux_validation_terminal_verdict_publish_requires_manual_action"] = False
    terminal_publish_payload["linux_validation_terminal_verdict_publish_channel"] = "follow_up"
    terminal_publish_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    terminal_publish_payload["reason_codes"] = [
        "linux_validation_terminal_verdict_publish_with_follow_up"
    ]

    publish_path = tmp_path / "ci_workflow_linux_validation_terminal_verdict_publish_output.json"
    publish_path.write_text(json.dumps(terminal_publish_payload, indent=2), encoding="utf-8")

    publish_report = gate.load_linux_validation_terminal_verdict_publish_report(publish_path)
    dispatch_payload = gate.build_linux_validation_terminal_dispatch_payload(
        publish_report,
        source_path=publish_path.resolve(),
    )
    outputs = gate.build_github_output_values(
        dispatch_payload,
        output_json=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch.json"
        ),
        output_markdown=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch.md"
        ),
    )

    assert outputs["workflow_linux_validation_terminal_dispatch_status"] == "ready_with_follow_up_dry_run"
    assert (
        outputs["workflow_linux_validation_terminal_dispatch_decision"]
        == "dispatch_linux_validation_terminal_with_follow_up"
    )
    assert outputs["workflow_linux_validation_terminal_dispatch_exit_code"] == "1"
    assert outputs["workflow_linux_validation_terminal_dispatch_should_dispatch"] == "true"
    assert outputs["workflow_linux_validation_terminal_dispatch_requires_manual_action"] == "false"
    assert outputs["workflow_linux_validation_terminal_dispatch_channel"] == "follow_up"
    assert outputs["workflow_linux_validation_terminal_dispatch_follow_up_queue_url"].endswith(
        "/issues/77"
    )
    assert outputs["workflow_linux_validation_terminal_dispatch_run_id"] == "1234567890"
    assert outputs["workflow_linux_validation_terminal_dispatch_run_url"].endswith(
        "/actions/runs/1234567890"
    )
    assert outputs["workflow_linux_validation_terminal_dispatch_report_json"].endswith(
        "ci_workflow_linux_validation_terminal_dispatch.json"
    )
    assert outputs["workflow_linux_validation_terminal_dispatch_report_markdown"].endswith(
        "ci_workflow_linux_validation_terminal_dispatch.md"
    )

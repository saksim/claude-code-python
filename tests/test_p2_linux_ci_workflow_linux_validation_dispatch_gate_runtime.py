"""Contract tests for P2-60 Linux CI workflow Linux validation dispatch gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_linux_validation_dispatch_gate_module():
    script_path = (
        Path("scripts") / "run_p2_linux_ci_workflow_linux_validation_dispatch_gate.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_linux_validation_dispatch_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_terminal_verdict_payload() -> dict:
    return {
        "generated_at": "2026-05-01T00:00:00+00:00",
        "source_release_final_publish_archive_report": "/tmp/ci_workflow_release_final_publish_archive.json",
        "source_gate_manifest_drift_report": "/tmp/linux_gate_manifest_drift.json",
        "source_release_final_verdict_publish_report": "/tmp/ci_workflow_release_final_verdict_publish.json",
        "source_release_final_verdict_report": "/tmp/ci_workflow_release_final_verdict.json",
        "source_release_final_archive_report": "/tmp/ci_workflow_release_final_archive.json",
        "source_release_final_closure_publish_report": "/tmp/ci_workflow_release_final_closure_publish.json",
        "source_release_final_closure_report": "/tmp/ci_workflow_release_final_closure.json",
        "source_release_final_handoff_report": "/tmp/ci_workflow_release_final_handoff.json",
        "source_release_final_terminal_publish_report": "/tmp/ci_workflow_release_final_terminal_publish.json",
        "source_release_final_outcome_report": "/tmp/ci_workflow_release_final_outcome.json",
        "source_release_delivery_final_verdict_report": "/tmp/ci_workflow_release_delivery_final_verdict.json",
        "source_release_follow_up_final_verdict_report": "/tmp/ci_workflow_release_follow_up_final_verdict.json",
        "release_delivery_final_verdict_status": "completed",
        "release_delivery_final_verdict_decision": "close_release",
        "release_delivery_final_verdict_exit_code": 0,
        "release_follow_up_final_verdict_status": "completed",
        "release_follow_up_final_verdict_decision": "close_follow_up",
        "release_follow_up_final_verdict_exit_code": 0,
        "release_final_outcome_status": "released",
        "release_final_outcome_decision": "ship_and_close",
        "release_final_outcome_exit_code": 0,
        "release_final_terminal_publish_status": "published",
        "release_final_terminal_publish_decision": "announce_release_closure",
        "release_final_terminal_publish_exit_code": 0,
        "release_final_handoff_status": "completed",
        "release_final_handoff_decision": "handoff_release_closure",
        "release_final_handoff_exit_code": 0,
        "release_final_closure_status": "closed",
        "release_final_closure_decision": "close_release",
        "release_final_closure_exit_code": 0,
        "release_final_closure_publish_status": "published",
        "release_final_closure_publish_decision": "announce_release_closed",
        "release_final_closure_publish_exit_code": 0,
        "release_final_archive_status": "archived",
        "release_final_archive_decision": "archive_release_closed",
        "release_final_archive_exit_code": 0,
        "release_final_verdict_status": "released",
        "release_final_verdict_decision": "ship_release",
        "release_final_verdict_exit_code": 0,
        "release_final_verdict_publish_status": "published",
        "release_final_verdict_publish_decision": "announce_release_shipped",
        "release_final_verdict_publish_exit_code": 0,
        "release_final_publish_archive_status": "archived",
        "release_final_publish_archive_decision": "archive_release_shipped",
        "release_final_publish_archive_exit_code": 0,
        "release_run_id": 1234567890,
        "release_run_url": "https://github.com/acme/demo/actions/runs/1234567890",
        "follow_up_queue_url": "",
        "gate_manifest_drift_status": "passed",
        "gate_manifest_drift_missing_runtime_tests": [],
        "gate_manifest_drift_missing_manifest_entries": [],
        "gate_manifest_drift_orphan_manifest_entries": [],
        "terminal_verdict_should_proceed": True,
        "terminal_verdict_requires_manual_action": False,
        "terminal_verdict_channel": "release",
        "terminal_verdict_status": "ready_for_linux_validation",
        "terminal_verdict_decision": "proceed_linux_validation",
        "terminal_verdict_exit_code": 0,
        "terminal_verdict_summary": (
            "release_final_publish_archive_status=archived "
            "gate_manifest_drift_status=passed "
            "terminal_verdict_status=ready_for_linux_validation "
            "terminal_verdict_decision=proceed_linux_validation"
        ),
        "reason_codes": ["terminal_verdict_ready_for_linux_validation"],
        "structural_issues": [],
        "missing_artifacts": [],
        "evidence_manifest": [
            {
                "source": "final_publish_archive",
                "path": "/tmp/ci_workflow_release_final_publish_archive.json",
                "exists": True,
            },
            {
                "source": "manifest_drift",
                "path": "/tmp/linux_gate_manifest_drift.json",
                "exists": True,
            },
        ],
    }


def test_build_linux_validation_dispatch_payload_ready_dry_run(tmp_path: Path):
    gate = _load_ci_workflow_linux_validation_dispatch_gate_module()
    terminal_payload = _sample_terminal_verdict_payload()

    terminal_path = tmp_path / "ci_workflow_terminal_verdict.json"
    terminal_path.write_text(json.dumps(terminal_payload, indent=2), encoding="utf-8")

    terminal_report = gate.load_terminal_verdict_report(terminal_path)
    command_parts = gate.build_linux_validation_command_parts(
        terminal_verdict_report=terminal_report,
        python_executable="python",
        linux_validation_command="",
    )
    payload = gate.build_linux_validation_dispatch_payload(
        terminal_report,
        source_path=terminal_path.resolve(),
        project_root=tmp_path.resolve(),
        linux_validation_timeout_seconds=7200,
        command_parts=command_parts,
        dry_run=True,
        command_result=None,
    )

    assert payload["linux_validation_dispatch_status"] == "ready_dry_run"
    assert payload["linux_validation_dispatch_decision"] == "dispatch_linux_validation"
    assert payload["linux_validation_dispatch_exit_code"] == 0
    assert payload["linux_validation_should_dispatch"] is True
    assert payload["linux_validation_requires_manual_action"] is False
    assert payload["linux_validation_channel"] == "release"
    assert payload["linux_validation_dispatch_attempted"] is False
    assert payload["linux_validation_command_parts"][:2] == [
        "python",
        "scripts/run_p2_linux_unified_pipeline_gate.py",
    ]


def test_build_linux_validation_dispatch_payload_ready_with_follow_up_dry_run(tmp_path: Path):
    gate = _load_ci_workflow_linux_validation_dispatch_gate_module()
    terminal_payload = _sample_terminal_verdict_payload()
    terminal_payload["release_follow_up_final_verdict_status"] = "requires_follow_up"
    terminal_payload["release_follow_up_final_verdict_decision"] = "keep_follow_up_open"
    terminal_payload["release_follow_up_final_verdict_exit_code"] = 1
    terminal_payload["release_final_outcome_status"] = "released_with_follow_up"
    terminal_payload["release_final_outcome_decision"] = "ship_with_follow_up_open"
    terminal_payload["release_final_outcome_exit_code"] = 1
    terminal_payload["release_final_terminal_publish_status"] = "published_with_follow_up"
    terminal_payload["release_final_terminal_publish_decision"] = (
        "announce_release_with_follow_up"
    )
    terminal_payload["release_final_terminal_publish_exit_code"] = 1
    terminal_payload["release_final_handoff_status"] = "completed_with_follow_up"
    terminal_payload["release_final_handoff_decision"] = "handoff_release_with_follow_up"
    terminal_payload["release_final_handoff_exit_code"] = 1
    terminal_payload["release_final_closure_status"] = "closed_with_follow_up"
    terminal_payload["release_final_closure_decision"] = "close_with_follow_up"
    terminal_payload["release_final_closure_exit_code"] = 1
    terminal_payload["release_final_closure_publish_status"] = "published_with_follow_up"
    terminal_payload["release_final_closure_publish_decision"] = (
        "announce_release_closed_with_follow_up"
    )
    terminal_payload["release_final_closure_publish_exit_code"] = 1
    terminal_payload["release_final_archive_status"] = "archived_with_follow_up"
    terminal_payload["release_final_archive_decision"] = (
        "archive_release_closed_with_follow_up"
    )
    terminal_payload["release_final_archive_exit_code"] = 1
    terminal_payload["release_final_verdict_status"] = "released_with_follow_up"
    terminal_payload["release_final_verdict_decision"] = "ship_release_with_follow_up"
    terminal_payload["release_final_verdict_exit_code"] = 1
    terminal_payload["release_final_verdict_publish_status"] = "published_with_follow_up"
    terminal_payload["release_final_verdict_publish_decision"] = (
        "announce_release_shipped_with_follow_up"
    )
    terminal_payload["release_final_verdict_publish_exit_code"] = 1
    terminal_payload["release_final_publish_archive_status"] = "archived_with_follow_up"
    terminal_payload["release_final_publish_archive_decision"] = (
        "archive_release_shipped_with_follow_up"
    )
    terminal_payload["release_final_publish_archive_exit_code"] = 1
    terminal_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    terminal_payload["terminal_verdict_channel"] = "follow_up"
    terminal_payload["terminal_verdict_status"] = "ready_with_follow_up_for_linux_validation"
    terminal_payload["terminal_verdict_decision"] = "proceed_linux_validation_with_follow_up"
    terminal_payload["terminal_verdict_exit_code"] = 1
    terminal_payload["terminal_verdict_summary"] = (
        "release_final_publish_archive_status=archived_with_follow_up "
        "gate_manifest_drift_status=passed "
        "terminal_verdict_status=ready_with_follow_up_for_linux_validation "
        "terminal_verdict_decision=proceed_linux_validation_with_follow_up"
    )
    terminal_payload["reason_codes"] = [
        "terminal_verdict_ready_with_follow_up_for_linux_validation"
    ]

    terminal_path = tmp_path / "ci_workflow_terminal_verdict_with_follow_up.json"
    terminal_path.write_text(json.dumps(terminal_payload, indent=2), encoding="utf-8")

    terminal_report = gate.load_terminal_verdict_report(terminal_path)
    command_parts = gate.build_linux_validation_command_parts(
        terminal_verdict_report=terminal_report,
        python_executable="python",
        linux_validation_command="",
    )
    payload = gate.build_linux_validation_dispatch_payload(
        terminal_report,
        source_path=terminal_path.resolve(),
        project_root=tmp_path.resolve(),
        linux_validation_timeout_seconds=7200,
        command_parts=command_parts,
        dry_run=True,
        command_result=None,
    )

    assert payload["linux_validation_dispatch_status"] == "ready_with_follow_up_dry_run"
    assert (
        payload["linux_validation_dispatch_decision"]
        == "dispatch_linux_validation_with_follow_up"
    )
    assert payload["linux_validation_dispatch_exit_code"] == 1
    assert payload["linux_validation_should_dispatch"] is True
    assert payload["linux_validation_requires_manual_action"] is False
    assert payload["linux_validation_channel"] == "follow_up"
    assert payload["follow_up_queue_url"].endswith("/issues/77")


def test_build_linux_validation_dispatch_payload_blocked(tmp_path: Path):
    gate = _load_ci_workflow_linux_validation_dispatch_gate_module()
    terminal_payload = _sample_terminal_verdict_payload()
    terminal_payload["release_delivery_final_verdict_status"] = "blocked"
    terminal_payload["release_delivery_final_verdict_decision"] = "escalate_blocker"
    terminal_payload["release_delivery_final_verdict_exit_code"] = 1
    terminal_payload["release_follow_up_final_verdict_status"] = "blocked"
    terminal_payload["release_follow_up_final_verdict_decision"] = "escalate_queue_failure"
    terminal_payload["release_follow_up_final_verdict_exit_code"] = 1
    terminal_payload["release_final_outcome_status"] = "blocked"
    terminal_payload["release_final_outcome_decision"] = "escalate_blocker"
    terminal_payload["release_final_outcome_exit_code"] = 1
    terminal_payload["release_final_terminal_publish_status"] = "blocked"
    terminal_payload["release_final_terminal_publish_decision"] = "announce_blocker"
    terminal_payload["release_final_terminal_publish_exit_code"] = 1
    terminal_payload["release_final_handoff_status"] = "blocked"
    terminal_payload["release_final_handoff_decision"] = "handoff_blocker"
    terminal_payload["release_final_handoff_exit_code"] = 1
    terminal_payload["release_final_closure_status"] = "blocked"
    terminal_payload["release_final_closure_decision"] = "close_blocker"
    terminal_payload["release_final_closure_exit_code"] = 1
    terminal_payload["release_final_closure_publish_status"] = "blocked"
    terminal_payload["release_final_closure_publish_decision"] = "announce_release_blocker"
    terminal_payload["release_final_closure_publish_exit_code"] = 1
    terminal_payload["release_final_archive_status"] = "blocked"
    terminal_payload["release_final_archive_decision"] = "archive_release_blocker"
    terminal_payload["release_final_archive_exit_code"] = 1
    terminal_payload["release_final_verdict_status"] = "blocked"
    terminal_payload["release_final_verdict_decision"] = "escalate_release_blocker"
    terminal_payload["release_final_verdict_exit_code"] = 1
    terminal_payload["release_final_verdict_publish_status"] = "blocked"
    terminal_payload["release_final_verdict_publish_decision"] = "announce_release_blocker"
    terminal_payload["release_final_verdict_publish_exit_code"] = 1
    terminal_payload["release_final_publish_archive_status"] = "blocked"
    terminal_payload["release_final_publish_archive_decision"] = "archive_release_blocker"
    terminal_payload["release_final_publish_archive_exit_code"] = 1
    terminal_payload["terminal_verdict_should_proceed"] = False
    terminal_payload["terminal_verdict_requires_manual_action"] = True
    terminal_payload["terminal_verdict_channel"] = "blocker"
    terminal_payload["terminal_verdict_status"] = "blocked"
    terminal_payload["terminal_verdict_decision"] = "halt_linux_validation_blocker"
    terminal_payload["terminal_verdict_exit_code"] = 1
    terminal_payload["terminal_verdict_summary"] = (
        "release_final_publish_archive_status=blocked "
        "gate_manifest_drift_status=passed "
        "terminal_verdict_status=blocked "
        "terminal_verdict_decision=halt_linux_validation_blocker"
    )
    terminal_payload["reason_codes"] = ["terminal_verdict_blocked"]

    terminal_path = tmp_path / "ci_workflow_terminal_verdict_blocked.json"
    terminal_path.write_text(json.dumps(terminal_payload, indent=2), encoding="utf-8")

    terminal_report = gate.load_terminal_verdict_report(terminal_path)
    command_parts = gate.build_linux_validation_command_parts(
        terminal_verdict_report=terminal_report,
        python_executable="python",
        linux_validation_command="",
    )
    payload = gate.build_linux_validation_dispatch_payload(
        terminal_report,
        source_path=terminal_path.resolve(),
        project_root=tmp_path.resolve(),
        linux_validation_timeout_seconds=7200,
        command_parts=command_parts,
        dry_run=False,
        command_result=None,
    )

    assert payload["linux_validation_dispatch_status"] == "blocked"
    assert payload["linux_validation_dispatch_decision"] == "hold_linux_validation_blocker"
    assert payload["linux_validation_dispatch_exit_code"] == 1
    assert payload["linux_validation_should_dispatch"] is False
    assert payload["linux_validation_requires_manual_action"] is True
    assert payload["linux_validation_channel"] == "blocker"
    assert payload["linux_validation_dispatch_attempted"] is False
    assert payload["linux_validation_command_parts"] == []


def test_build_linux_validation_dispatch_payload_rejects_contract_mismatch_and_drift_failure(
    tmp_path: Path,
):
    gate = _load_ci_workflow_linux_validation_dispatch_gate_module()
    terminal_payload = _sample_terminal_verdict_payload()
    terminal_payload["terminal_verdict_status"] = "ready_for_linux_validation"
    terminal_payload["terminal_verdict_decision"] = "halt_linux_validation_blocker"
    terminal_payload["terminal_verdict_should_proceed"] = False
    terminal_payload["terminal_verdict_requires_manual_action"] = True
    terminal_payload["terminal_verdict_channel"] = "blocker"
    terminal_payload["gate_manifest_drift_status"] = "failed"
    terminal_payload["gate_manifest_drift_missing_runtime_tests"] = [
        "test_missing_gate_runtime.py"
    ]
    terminal_payload["gate_manifest_drift_missing_manifest_entries"] = [
        "tests/test_missing_gate_runtime.py"
    ]
    terminal_payload["gate_manifest_drift_orphan_manifest_entries"] = [
        "tests/test_orphan_gate_runtime.py"
    ]
    terminal_payload["evidence_manifest"][1]["exists"] = False

    terminal_path = tmp_path / "ci_workflow_terminal_verdict_mismatch.json"
    terminal_path.write_text(json.dumps(terminal_payload, indent=2), encoding="utf-8")

    terminal_report = gate.load_terminal_verdict_report(terminal_path)
    command_parts = gate.build_linux_validation_command_parts(
        terminal_verdict_report=terminal_report,
        python_executable="python",
        linux_validation_command="",
    )
    payload = gate.build_linux_validation_dispatch_payload(
        terminal_report,
        source_path=terminal_path.resolve(),
        project_root=tmp_path.resolve(),
        linux_validation_timeout_seconds=7200,
        command_parts=command_parts,
        dry_run=False,
        command_result=None,
    )

    assert payload["linux_validation_dispatch_status"] == "contract_failed"
    assert payload["linux_validation_dispatch_decision"] == "abort_linux_validation_dispatch"
    assert payload["linux_validation_dispatch_exit_code"] == 1
    assert payload["linux_validation_should_dispatch"] is False
    assert payload["linux_validation_requires_manual_action"] is True
    assert payload["linux_validation_channel"] == "blocker"
    assert "terminal_verdict_decision_mismatch" in payload["structural_issues"]
    assert "gate_manifest_drift_failed" in payload["structural_issues"]
    assert "terminal_verdict_evidence_missing" in payload["structural_issues"]


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_linux_validation_dispatch_gate_module()
    terminal_payload = _sample_terminal_verdict_payload()
    terminal_payload["release_follow_up_final_verdict_status"] = "requires_follow_up"
    terminal_payload["release_follow_up_final_verdict_decision"] = "keep_follow_up_open"
    terminal_payload["release_follow_up_final_verdict_exit_code"] = 1
    terminal_payload["release_final_outcome_status"] = "released_with_follow_up"
    terminal_payload["release_final_outcome_decision"] = "ship_with_follow_up_open"
    terminal_payload["release_final_outcome_exit_code"] = 1
    terminal_payload["release_final_terminal_publish_status"] = "published_with_follow_up"
    terminal_payload["release_final_terminal_publish_decision"] = (
        "announce_release_with_follow_up"
    )
    terminal_payload["release_final_terminal_publish_exit_code"] = 1
    terminal_payload["release_final_handoff_status"] = "completed_with_follow_up"
    terminal_payload["release_final_handoff_decision"] = "handoff_release_with_follow_up"
    terminal_payload["release_final_handoff_exit_code"] = 1
    terminal_payload["release_final_closure_status"] = "closed_with_follow_up"
    terminal_payload["release_final_closure_decision"] = "close_with_follow_up"
    terminal_payload["release_final_closure_exit_code"] = 1
    terminal_payload["release_final_closure_publish_status"] = "published_with_follow_up"
    terminal_payload["release_final_closure_publish_decision"] = (
        "announce_release_closed_with_follow_up"
    )
    terminal_payload["release_final_closure_publish_exit_code"] = 1
    terminal_payload["release_final_archive_status"] = "archived_with_follow_up"
    terminal_payload["release_final_archive_decision"] = (
        "archive_release_closed_with_follow_up"
    )
    terminal_payload["release_final_archive_exit_code"] = 1
    terminal_payload["release_final_verdict_status"] = "released_with_follow_up"
    terminal_payload["release_final_verdict_decision"] = "ship_release_with_follow_up"
    terminal_payload["release_final_verdict_exit_code"] = 1
    terminal_payload["release_final_verdict_publish_status"] = "published_with_follow_up"
    terminal_payload["release_final_verdict_publish_decision"] = (
        "announce_release_shipped_with_follow_up"
    )
    terminal_payload["release_final_verdict_publish_exit_code"] = 1
    terminal_payload["release_final_publish_archive_status"] = "archived_with_follow_up"
    terminal_payload["release_final_publish_archive_decision"] = (
        "archive_release_shipped_with_follow_up"
    )
    terminal_payload["release_final_publish_archive_exit_code"] = 1
    terminal_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    terminal_payload["terminal_verdict_channel"] = "follow_up"
    terminal_payload["terminal_verdict_status"] = "ready_with_follow_up_for_linux_validation"
    terminal_payload["terminal_verdict_decision"] = "proceed_linux_validation_with_follow_up"
    terminal_payload["terminal_verdict_exit_code"] = 1
    terminal_payload["reason_codes"] = [
        "terminal_verdict_ready_with_follow_up_for_linux_validation"
    ]

    terminal_path = tmp_path / "ci_workflow_terminal_verdict_outputs.json"
    terminal_path.write_text(json.dumps(terminal_payload, indent=2), encoding="utf-8")

    terminal_report = gate.load_terminal_verdict_report(terminal_path)
    command_parts = gate.build_linux_validation_command_parts(
        terminal_verdict_report=terminal_report,
        python_executable="python",
        linux_validation_command="python scripts/run_p2_linux_unified_pipeline_gate.py --dry-run",
    )
    payload = gate.build_linux_validation_dispatch_payload(
        terminal_report,
        source_path=terminal_path.resolve(),
        project_root=tmp_path.resolve(),
        linux_validation_timeout_seconds=7200,
        command_parts=command_parts,
        dry_run=True,
        command_result=None,
    )
    outputs = gate.build_github_output_values(
        payload,
        output_json=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_linux_validation_dispatch.json"
        ),
        output_markdown=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_linux_validation_dispatch.md"
        ),
    )

    assert outputs["workflow_linux_validation_dispatch_status"] == "ready_with_follow_up_dry_run"
    assert (
        outputs["workflow_linux_validation_dispatch_decision"]
        == "dispatch_linux_validation_with_follow_up"
    )
    assert outputs["workflow_linux_validation_dispatch_exit_code"] == "1"
    assert outputs["workflow_linux_validation_dispatch_should_dispatch"] == "true"
    assert outputs["workflow_linux_validation_dispatch_requires_manual_action"] == "false"
    assert outputs["workflow_linux_validation_dispatch_channel"] == "follow_up"
    assert outputs["workflow_linux_validation_dispatch_attempted"] == "false"
    assert outputs["workflow_linux_validation_dispatch_command_returncode"] == ""
    assert (
        outputs["workflow_linux_validation_dispatch_terminal_verdict_status"]
        == "ready_with_follow_up_for_linux_validation"
    )
    assert outputs["workflow_linux_validation_dispatch_gate_manifest_drift_status"] == "passed"
    assert outputs["workflow_linux_validation_dispatch_follow_up_queue_url"].endswith(
        "/issues/77"
    )
    assert outputs["workflow_linux_validation_dispatch_run_id"] == "1234567890"
    assert outputs["workflow_linux_validation_dispatch_run_url"].endswith(
        "/actions/runs/1234567890"
    )
    assert outputs["workflow_linux_validation_dispatch_report_json"].endswith(
        "ci_workflow_linux_validation_dispatch.json"
    )
    assert outputs["workflow_linux_validation_dispatch_report_markdown"].endswith(
        "ci_workflow_linux_validation_dispatch.md"
    )


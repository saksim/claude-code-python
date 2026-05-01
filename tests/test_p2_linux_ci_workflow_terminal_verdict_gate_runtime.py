"""Contract tests for P2-59 Linux CI workflow terminal verdict gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_terminal_verdict_gate_module():
    script_path = Path("scripts") / "run_p2_linux_ci_workflow_terminal_verdict_gate.py"
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_terminal_verdict_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_release_final_publish_archive_payload() -> dict:
    return {
        "generated_at": "2026-05-01T00:00:00+00:00",
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
        "release_run_id": 1234567890,
        "release_run_url": "https://github.com/acme/demo/actions/runs/1234567890",
        "follow_up_queue_url": "",
        "final_publish_archive_should_archive": True,
        "final_publish_archive_requires_manual_action": False,
        "final_publish_archive_channel": "release",
        "release_final_publish_archive_status": "archived",
        "release_final_publish_archive_decision": "archive_release_shipped",
        "release_final_publish_archive_exit_code": 0,
        "release_final_publish_archive_summary": (
            "release_final_verdict_publish_status=published "
            "release_final_publish_archive_status=archived "
            "release_final_publish_archive_decision=archive_release_shipped"
        ),
        "reason_codes": ["release_final_publish_archive_archived"],
        "structural_issues": [],
        "missing_artifacts": [],
        "evidence_manifest": [
            {
                "source": "final_verdict_publish",
                "path": "/tmp/ci_workflow_release_final_verdict_publish.json",
                "exists": True,
            },
            {
                "source": "final_verdict",
                "path": "/tmp/ci_workflow_release_final_verdict.json",
                "exists": True,
            },
        ],
    }


def _sample_gate_manifest_drift_payload() -> dict:
    return {
        "status": "passed",
        "missing_runtime_tests": [],
        "missing_manifest_entries": [],
        "orphan_manifest_entries": [],
        "structural_issues": [],
    }


def test_build_terminal_verdict_payload_ready_for_linux_validation(tmp_path: Path):
    gate = _load_ci_workflow_terminal_verdict_gate_module()
    publish_archive_payload = _sample_release_final_publish_archive_payload()
    drift_payload = _sample_gate_manifest_drift_payload()

    publish_archive_path = tmp_path / "release_final_publish_archive.json"
    drift_path = tmp_path / "linux_gate_manifest_drift.json"
    publish_archive_path.write_text(
        json.dumps(publish_archive_payload, indent=2),
        encoding="utf-8",
    )
    drift_path.write_text(json.dumps(drift_payload, indent=2), encoding="utf-8")

    publish_archive_report = gate.load_release_final_publish_archive_report(publish_archive_path)
    drift_report = gate.load_gate_manifest_drift_report(drift_path)
    payload = gate.build_terminal_verdict_payload(
        publish_archive_report,
        drift_report,
        release_source_path=publish_archive_path.resolve(),
        drift_source_path=drift_path.resolve(),
    )

    assert payload["terminal_verdict_status"] == "ready_for_linux_validation"
    assert payload["terminal_verdict_decision"] == "proceed_linux_validation"
    assert payload["terminal_verdict_exit_code"] == 0
    assert payload["terminal_verdict_should_proceed"] is True
    assert payload["terminal_verdict_requires_manual_action"] is False
    assert payload["terminal_verdict_channel"] == "release"
    assert payload["gate_manifest_drift_status"] == "passed"
    assert payload["gate_manifest_drift_missing_runtime_tests"] == []
    assert payload["gate_manifest_drift_missing_manifest_entries"] == []
    assert payload["gate_manifest_drift_orphan_manifest_entries"] == []


def test_build_terminal_verdict_payload_ready_with_follow_up_for_linux_validation(tmp_path: Path):
    gate = _load_ci_workflow_terminal_verdict_gate_module()
    publish_archive_payload = _sample_release_final_publish_archive_payload()
    publish_archive_payload["release_follow_up_final_verdict_status"] = "requires_follow_up"
    publish_archive_payload["release_follow_up_final_verdict_decision"] = "keep_follow_up_open"
    publish_archive_payload["release_follow_up_final_verdict_exit_code"] = 1
    publish_archive_payload["release_final_outcome_status"] = "released_with_follow_up"
    publish_archive_payload["release_final_outcome_decision"] = "ship_with_follow_up_open"
    publish_archive_payload["release_final_outcome_exit_code"] = 1
    publish_archive_payload["release_final_terminal_publish_status"] = "published_with_follow_up"
    publish_archive_payload["release_final_terminal_publish_decision"] = (
        "announce_release_with_follow_up"
    )
    publish_archive_payload["release_final_terminal_publish_exit_code"] = 1
    publish_archive_payload["release_final_handoff_status"] = "completed_with_follow_up"
    publish_archive_payload["release_final_handoff_decision"] = "handoff_release_with_follow_up"
    publish_archive_payload["release_final_handoff_exit_code"] = 1
    publish_archive_payload["release_final_closure_status"] = "closed_with_follow_up"
    publish_archive_payload["release_final_closure_decision"] = "close_with_follow_up"
    publish_archive_payload["release_final_closure_exit_code"] = 1
    publish_archive_payload["release_final_closure_publish_status"] = "published_with_follow_up"
    publish_archive_payload["release_final_closure_publish_decision"] = (
        "announce_release_closed_with_follow_up"
    )
    publish_archive_payload["release_final_closure_publish_exit_code"] = 1
    publish_archive_payload["release_final_archive_status"] = "archived_with_follow_up"
    publish_archive_payload["release_final_archive_decision"] = (
        "archive_release_closed_with_follow_up"
    )
    publish_archive_payload["release_final_archive_exit_code"] = 1
    publish_archive_payload["release_final_verdict_status"] = "released_with_follow_up"
    publish_archive_payload["release_final_verdict_decision"] = "ship_release_with_follow_up"
    publish_archive_payload["release_final_verdict_exit_code"] = 1
    publish_archive_payload["release_final_verdict_publish_status"] = "published_with_follow_up"
    publish_archive_payload["release_final_verdict_publish_decision"] = (
        "announce_release_shipped_with_follow_up"
    )
    publish_archive_payload["release_final_verdict_publish_exit_code"] = 1
    publish_archive_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    publish_archive_payload["final_publish_archive_should_archive"] = True
    publish_archive_payload["final_publish_archive_requires_manual_action"] = False
    publish_archive_payload["final_publish_archive_channel"] = "follow_up"
    publish_archive_payload["release_final_publish_archive_status"] = "archived_with_follow_up"
    publish_archive_payload["release_final_publish_archive_decision"] = (
        "archive_release_shipped_with_follow_up"
    )
    publish_archive_payload["release_final_publish_archive_exit_code"] = 1
    publish_archive_payload["reason_codes"] = [
        "release_final_publish_archive_archived_with_follow_up"
    ]

    drift_payload = _sample_gate_manifest_drift_payload()

    publish_archive_path = tmp_path / "release_final_publish_archive_with_follow_up.json"
    drift_path = tmp_path / "linux_gate_manifest_drift.json"
    publish_archive_path.write_text(
        json.dumps(publish_archive_payload, indent=2),
        encoding="utf-8",
    )
    drift_path.write_text(json.dumps(drift_payload, indent=2), encoding="utf-8")

    publish_archive_report = gate.load_release_final_publish_archive_report(publish_archive_path)
    drift_report = gate.load_gate_manifest_drift_report(drift_path)
    payload = gate.build_terminal_verdict_payload(
        publish_archive_report,
        drift_report,
        release_source_path=publish_archive_path.resolve(),
        drift_source_path=drift_path.resolve(),
    )

    assert payload["terminal_verdict_status"] == "ready_with_follow_up_for_linux_validation"
    assert payload["terminal_verdict_decision"] == "proceed_linux_validation_with_follow_up"
    assert payload["terminal_verdict_exit_code"] == 1
    assert payload["terminal_verdict_should_proceed"] is True
    assert payload["terminal_verdict_requires_manual_action"] is False
    assert payload["terminal_verdict_channel"] == "follow_up"


def test_build_terminal_verdict_payload_blocked(tmp_path: Path):
    gate = _load_ci_workflow_terminal_verdict_gate_module()
    publish_archive_payload = _sample_release_final_publish_archive_payload()
    publish_archive_payload["release_delivery_final_verdict_status"] = "blocked"
    publish_archive_payload["release_delivery_final_verdict_decision"] = "escalate_blocker"
    publish_archive_payload["release_delivery_final_verdict_exit_code"] = 1
    publish_archive_payload["release_follow_up_final_verdict_status"] = "blocked"
    publish_archive_payload["release_follow_up_final_verdict_decision"] = (
        "escalate_queue_failure"
    )
    publish_archive_payload["release_follow_up_final_verdict_exit_code"] = 1
    publish_archive_payload["release_final_outcome_status"] = "blocked"
    publish_archive_payload["release_final_outcome_decision"] = "escalate_blocker"
    publish_archive_payload["release_final_outcome_exit_code"] = 1
    publish_archive_payload["release_final_terminal_publish_status"] = "blocked"
    publish_archive_payload["release_final_terminal_publish_decision"] = "announce_blocker"
    publish_archive_payload["release_final_terminal_publish_exit_code"] = 1
    publish_archive_payload["release_final_handoff_status"] = "blocked"
    publish_archive_payload["release_final_handoff_decision"] = "handoff_blocker"
    publish_archive_payload["release_final_handoff_exit_code"] = 1
    publish_archive_payload["release_final_closure_status"] = "blocked"
    publish_archive_payload["release_final_closure_decision"] = "close_blocker"
    publish_archive_payload["release_final_closure_exit_code"] = 1
    publish_archive_payload["release_final_closure_publish_status"] = "blocked"
    publish_archive_payload["release_final_closure_publish_decision"] = "announce_release_blocker"
    publish_archive_payload["release_final_closure_publish_exit_code"] = 1
    publish_archive_payload["release_final_archive_status"] = "blocked"
    publish_archive_payload["release_final_archive_decision"] = "archive_release_blocker"
    publish_archive_payload["release_final_archive_exit_code"] = 1
    publish_archive_payload["release_final_verdict_status"] = "blocked"
    publish_archive_payload["release_final_verdict_decision"] = "escalate_release_blocker"
    publish_archive_payload["release_final_verdict_exit_code"] = 1
    publish_archive_payload["release_final_verdict_publish_status"] = "blocked"
    publish_archive_payload["release_final_verdict_publish_decision"] = "announce_release_blocker"
    publish_archive_payload["release_final_verdict_publish_exit_code"] = 1
    publish_archive_payload["final_publish_archive_should_archive"] = False
    publish_archive_payload["final_publish_archive_requires_manual_action"] = True
    publish_archive_payload["final_publish_archive_channel"] = "blocker"
    publish_archive_payload["release_final_publish_archive_status"] = "blocked"
    publish_archive_payload["release_final_publish_archive_decision"] = "archive_release_blocker"
    publish_archive_payload["release_final_publish_archive_exit_code"] = 1
    publish_archive_payload["reason_codes"] = ["release_final_publish_archive_blocked"]

    drift_payload = _sample_gate_manifest_drift_payload()

    publish_archive_path = tmp_path / "release_final_publish_archive_blocked.json"
    drift_path = tmp_path / "linux_gate_manifest_drift.json"
    publish_archive_path.write_text(
        json.dumps(publish_archive_payload, indent=2),
        encoding="utf-8",
    )
    drift_path.write_text(json.dumps(drift_payload, indent=2), encoding="utf-8")

    publish_archive_report = gate.load_release_final_publish_archive_report(publish_archive_path)
    drift_report = gate.load_gate_manifest_drift_report(drift_path)
    payload = gate.build_terminal_verdict_payload(
        publish_archive_report,
        drift_report,
        release_source_path=publish_archive_path.resolve(),
        drift_source_path=drift_path.resolve(),
    )

    assert payload["terminal_verdict_status"] == "blocked"
    assert payload["terminal_verdict_decision"] == "halt_linux_validation_blocker"
    assert payload["terminal_verdict_exit_code"] == 1
    assert payload["terminal_verdict_should_proceed"] is False
    assert payload["terminal_verdict_requires_manual_action"] is True
    assert payload["terminal_verdict_channel"] == "blocker"


def test_build_terminal_verdict_payload_rejects_mismatch_and_drift_failure(tmp_path: Path):
    gate = _load_ci_workflow_terminal_verdict_gate_module()
    publish_archive_payload = _sample_release_final_publish_archive_payload()
    publish_archive_payload["release_final_publish_archive_status"] = "archived"
    publish_archive_payload["release_final_publish_archive_decision"] = "archive_release_blocker"
    publish_archive_payload["final_publish_archive_should_archive"] = False
    publish_archive_payload["final_publish_archive_requires_manual_action"] = True
    publish_archive_payload["final_publish_archive_channel"] = "blocker"

    drift_payload = _sample_gate_manifest_drift_payload()
    drift_payload["status"] = "failed"
    drift_payload["missing_runtime_tests"] = ["test_missing_gate_runtime.py"]
    drift_payload["missing_manifest_entries"] = ["tests/test_missing_gate_runtime.py"]
    drift_payload["orphan_manifest_entries"] = ["tests/test_orphan_gate_runtime.py"]
    drift_payload["structural_issues"] = ["missing_gate_runtime_tests"]

    publish_archive_path = tmp_path / "release_final_publish_archive_mismatch.json"
    drift_path = tmp_path / "linux_gate_manifest_drift_failed.json"
    publish_archive_path.write_text(
        json.dumps(publish_archive_payload, indent=2),
        encoding="utf-8",
    )
    drift_path.write_text(json.dumps(drift_payload, indent=2), encoding="utf-8")

    publish_archive_report = gate.load_release_final_publish_archive_report(publish_archive_path)
    drift_report = gate.load_gate_manifest_drift_report(drift_path)
    payload = gate.build_terminal_verdict_payload(
        publish_archive_report,
        drift_report,
        release_source_path=publish_archive_path.resolve(),
        drift_source_path=drift_path.resolve(),
    )

    assert payload["terminal_verdict_status"] == "contract_failed"
    assert payload["terminal_verdict_decision"] == "abort_linux_validation"
    assert payload["terminal_verdict_exit_code"] == 1
    assert payload["terminal_verdict_should_proceed"] is False
    assert payload["terminal_verdict_requires_manual_action"] is True
    assert payload["terminal_verdict_channel"] == "blocker"
    assert "final_publish_archive_decision_mismatch" in payload["structural_issues"]
    assert "gate_manifest_drift_failed" in payload["structural_issues"]
    assert "gate_manifest_drift_missing_runtime_tests" in payload["structural_issues"]


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_terminal_verdict_gate_module()
    publish_archive_payload = _sample_release_final_publish_archive_payload()
    publish_archive_payload["release_follow_up_final_verdict_status"] = "requires_follow_up"
    publish_archive_payload["release_follow_up_final_verdict_decision"] = "keep_follow_up_open"
    publish_archive_payload["release_follow_up_final_verdict_exit_code"] = 1
    publish_archive_payload["release_final_outcome_status"] = "released_with_follow_up"
    publish_archive_payload["release_final_outcome_decision"] = "ship_with_follow_up_open"
    publish_archive_payload["release_final_outcome_exit_code"] = 1
    publish_archive_payload["release_final_terminal_publish_status"] = "published_with_follow_up"
    publish_archive_payload["release_final_terminal_publish_decision"] = (
        "announce_release_with_follow_up"
    )
    publish_archive_payload["release_final_terminal_publish_exit_code"] = 1
    publish_archive_payload["release_final_handoff_status"] = "completed_with_follow_up"
    publish_archive_payload["release_final_handoff_decision"] = "handoff_release_with_follow_up"
    publish_archive_payload["release_final_handoff_exit_code"] = 1
    publish_archive_payload["release_final_closure_status"] = "closed_with_follow_up"
    publish_archive_payload["release_final_closure_decision"] = "close_with_follow_up"
    publish_archive_payload["release_final_closure_exit_code"] = 1
    publish_archive_payload["release_final_closure_publish_status"] = "published_with_follow_up"
    publish_archive_payload["release_final_closure_publish_decision"] = (
        "announce_release_closed_with_follow_up"
    )
    publish_archive_payload["release_final_closure_publish_exit_code"] = 1
    publish_archive_payload["release_final_archive_status"] = "archived_with_follow_up"
    publish_archive_payload["release_final_archive_decision"] = (
        "archive_release_closed_with_follow_up"
    )
    publish_archive_payload["release_final_archive_exit_code"] = 1
    publish_archive_payload["release_final_verdict_status"] = "released_with_follow_up"
    publish_archive_payload["release_final_verdict_decision"] = "ship_release_with_follow_up"
    publish_archive_payload["release_final_verdict_exit_code"] = 1
    publish_archive_payload["release_final_verdict_publish_status"] = "published_with_follow_up"
    publish_archive_payload["release_final_verdict_publish_decision"] = (
        "announce_release_shipped_with_follow_up"
    )
    publish_archive_payload["release_final_verdict_publish_exit_code"] = 1
    publish_archive_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    publish_archive_payload["final_publish_archive_should_archive"] = True
    publish_archive_payload["final_publish_archive_requires_manual_action"] = False
    publish_archive_payload["final_publish_archive_channel"] = "follow_up"
    publish_archive_payload["release_final_publish_archive_status"] = "archived_with_follow_up"
    publish_archive_payload["release_final_publish_archive_decision"] = (
        "archive_release_shipped_with_follow_up"
    )
    publish_archive_payload["release_final_publish_archive_exit_code"] = 1
    publish_archive_payload["reason_codes"] = [
        "release_final_publish_archive_archived_with_follow_up"
    ]

    drift_payload = _sample_gate_manifest_drift_payload()

    publish_archive_path = tmp_path / "release_final_publish_archive_with_follow_up.json"
    drift_path = tmp_path / "linux_gate_manifest_drift.json"
    publish_archive_path.write_text(
        json.dumps(publish_archive_payload, indent=2),
        encoding="utf-8",
    )
    drift_path.write_text(json.dumps(drift_payload, indent=2), encoding="utf-8")

    publish_archive_report = gate.load_release_final_publish_archive_report(publish_archive_path)
    drift_report = gate.load_gate_manifest_drift_report(drift_path)
    payload = gate.build_terminal_verdict_payload(
        publish_archive_report,
        drift_report,
        release_source_path=publish_archive_path.resolve(),
        drift_source_path=drift_path.resolve(),
    )
    outputs = gate.build_github_output_values(
        payload,
        output_json=Path(".claude/reports/linux_unified_gate/ci_workflow_terminal_verdict.json"),
        output_markdown=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_terminal_verdict.md"
        ),
    )

    assert outputs["workflow_terminal_verdict_status"] == "ready_with_follow_up_for_linux_validation"
    assert (
        outputs["workflow_terminal_verdict_decision"]
        == "proceed_linux_validation_with_follow_up"
    )
    assert outputs["workflow_terminal_verdict_exit_code"] == "1"
    assert outputs["workflow_terminal_verdict_should_proceed"] == "true"
    assert outputs["workflow_terminal_verdict_requires_manual_action"] == "false"
    assert outputs["workflow_terminal_verdict_channel"] == "follow_up"
    assert outputs["workflow_terminal_verdict_gate_manifest_drift_status"] == "passed"
    assert (
        outputs["workflow_terminal_verdict_gate_manifest_drift_missing_runtime_tests"]
        == "0"
    )
    assert (
        outputs["workflow_terminal_verdict_gate_manifest_drift_missing_manifest_entries"]
        == "0"
    )
    assert (
        outputs["workflow_terminal_verdict_gate_manifest_drift_orphan_manifest_entries"]
        == "0"
    )
    assert outputs["workflow_terminal_verdict_release_final_publish_archive_status"] == (
        "archived_with_follow_up"
    )
    assert outputs["workflow_terminal_verdict_follow_up_queue_url"].endswith("/issues/77")
    assert outputs["workflow_terminal_verdict_run_id"] == "1234567890"
    assert outputs["workflow_terminal_verdict_run_url"].endswith("/actions/runs/1234567890")
    assert outputs["workflow_terminal_verdict_report_json"].endswith(
        "ci_workflow_terminal_verdict.json"
    )
    assert outputs["workflow_terminal_verdict_report_markdown"].endswith(
        "ci_workflow_terminal_verdict.md"
    )

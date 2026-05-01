"""Contract tests for P2-53 Linux CI workflow release final archive gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_release_final_archive_gate_module():
    script_path = Path("scripts") / "run_p2_linux_ci_workflow_release_final_archive_gate.py"
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_release_final_archive_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_release_final_closure_publish_payload() -> dict:
    return {
        "generated_at": "2026-05-01T00:00:00+00:00",
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
        "release_run_id": 1234567890,
        "release_run_url": "https://github.com/acme/demo/actions/runs/1234567890",
        "follow_up_queue_url": "",
        "final_closure_publish_should_notify": True,
        "final_closure_publish_requires_manual_action": False,
        "final_closure_publish_channel": "release",
        "release_final_closure_publish_summary": (
            "release_final_closure_status=closed "
            "release_final_closure_publish_status=published "
            "release_final_closure_publish_decision=announce_release_closed"
        ),
        "reason_codes": ["release_final_closure_publish_published"],
        "structural_issues": [],
        "missing_artifacts": [],
        "evidence_manifest": [
            {
                "source": "final_closure",
                "path": "/tmp/ci_workflow_release_final_closure.json",
                "exists": True,
            },
            {
                "source": "final_handoff",
                "path": "/tmp/ci_workflow_release_final_handoff.json",
                "exists": True,
            },
        ],
    }


def test_build_release_final_archive_payload_archived(tmp_path: Path):
    gate = _load_ci_workflow_release_final_archive_gate_module()
    publish_payload = _sample_release_final_closure_publish_payload()

    publish_path = tmp_path / "ci_workflow_release_final_closure_publish.json"
    publish_path.write_text(json.dumps(publish_payload, indent=2), encoding="utf-8")

    publish_report = gate.load_release_final_closure_publish_report(publish_path)
    archive_payload = gate.build_release_final_archive_payload(
        publish_report,
        source_path=publish_path.resolve(),
    )

    assert archive_payload["release_final_archive_status"] == "archived"
    assert archive_payload["release_final_archive_decision"] == "archive_release_closed"
    assert archive_payload["release_final_archive_exit_code"] == 0
    assert archive_payload["final_archive_should_publish"] is True
    assert archive_payload["final_archive_requires_manual_action"] is False
    assert archive_payload["final_archive_channel"] == "release"
    assert "release_final_archive_archived" in archive_payload["reason_codes"]


def test_build_release_final_archive_payload_archived_with_follow_up(tmp_path: Path):
    gate = _load_ci_workflow_release_final_archive_gate_module()
    publish_payload = _sample_release_final_closure_publish_payload()
    publish_payload["release_follow_up_final_verdict_status"] = "requires_follow_up"
    publish_payload["release_follow_up_final_verdict_decision"] = "keep_follow_up_open"
    publish_payload["release_follow_up_final_verdict_exit_code"] = 1
    publish_payload["release_final_outcome_status"] = "released_with_follow_up"
    publish_payload["release_final_outcome_decision"] = "ship_with_follow_up_open"
    publish_payload["release_final_outcome_exit_code"] = 1
    publish_payload["release_final_terminal_publish_status"] = "published_with_follow_up"
    publish_payload["release_final_terminal_publish_decision"] = "announce_release_with_follow_up"
    publish_payload["release_final_terminal_publish_exit_code"] = 1
    publish_payload["release_final_handoff_status"] = "completed_with_follow_up"
    publish_payload["release_final_handoff_decision"] = "handoff_release_with_follow_up"
    publish_payload["release_final_handoff_exit_code"] = 1
    publish_payload["release_final_closure_status"] = "closed_with_follow_up"
    publish_payload["release_final_closure_decision"] = "close_with_follow_up"
    publish_payload["release_final_closure_exit_code"] = 1
    publish_payload["release_final_closure_publish_status"] = "published_with_follow_up"
    publish_payload["release_final_closure_publish_decision"] = (
        "announce_release_closed_with_follow_up"
    )
    publish_payload["release_final_closure_publish_exit_code"] = 1
    publish_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    publish_payload["final_closure_publish_should_notify"] = True
    publish_payload["final_closure_publish_requires_manual_action"] = False
    publish_payload["final_closure_publish_channel"] = "follow_up"
    publish_payload["reason_codes"] = ["release_final_closure_publish_with_follow_up"]

    publish_path = tmp_path / "release_final_closure_publish_with_follow_up.json"
    publish_path.write_text(json.dumps(publish_payload, indent=2), encoding="utf-8")

    publish_report = gate.load_release_final_closure_publish_report(publish_path)
    archive_payload = gate.build_release_final_archive_payload(
        publish_report,
        source_path=publish_path.resolve(),
    )

    assert archive_payload["release_final_archive_status"] == "archived_with_follow_up"
    assert (
        archive_payload["release_final_archive_decision"]
        == "archive_release_closed_with_follow_up"
    )
    assert archive_payload["release_final_archive_exit_code"] == 1
    assert archive_payload["final_archive_should_publish"] is True
    assert archive_payload["final_archive_requires_manual_action"] is False
    assert archive_payload["final_archive_channel"] == "follow_up"
    assert "release_final_archive_archived_with_follow_up" in archive_payload["reason_codes"]


def test_build_release_final_archive_payload_blocked(tmp_path: Path):
    gate = _load_ci_workflow_release_final_archive_gate_module()
    publish_payload = _sample_release_final_closure_publish_payload()
    publish_payload["release_delivery_final_verdict_status"] = "blocked"
    publish_payload["release_delivery_final_verdict_decision"] = "escalate_blocker"
    publish_payload["release_delivery_final_verdict_exit_code"] = 1
    publish_payload["release_follow_up_final_verdict_status"] = "blocked"
    publish_payload["release_follow_up_final_verdict_decision"] = "escalate_queue_failure"
    publish_payload["release_follow_up_final_verdict_exit_code"] = 1
    publish_payload["release_final_outcome_status"] = "blocked"
    publish_payload["release_final_outcome_decision"] = "escalate_blocker"
    publish_payload["release_final_outcome_exit_code"] = 1
    publish_payload["release_final_terminal_publish_status"] = "blocked"
    publish_payload["release_final_terminal_publish_decision"] = "announce_blocker"
    publish_payload["release_final_terminal_publish_exit_code"] = 1
    publish_payload["release_final_handoff_status"] = "blocked"
    publish_payload["release_final_handoff_decision"] = "handoff_blocker"
    publish_payload["release_final_handoff_exit_code"] = 1
    publish_payload["release_final_closure_status"] = "blocked"
    publish_payload["release_final_closure_decision"] = "close_blocker"
    publish_payload["release_final_closure_exit_code"] = 1
    publish_payload["release_final_closure_publish_status"] = "blocked"
    publish_payload["release_final_closure_publish_decision"] = "announce_release_blocker"
    publish_payload["release_final_closure_publish_exit_code"] = 1
    publish_payload["final_closure_publish_should_notify"] = True
    publish_payload["final_closure_publish_requires_manual_action"] = True
    publish_payload["final_closure_publish_channel"] = "blocker"
    publish_payload["reason_codes"] = ["release_final_closure_publish_blocked"]

    publish_path = tmp_path / "release_final_closure_publish_blocked.json"
    publish_path.write_text(json.dumps(publish_payload, indent=2), encoding="utf-8")

    publish_report = gate.load_release_final_closure_publish_report(publish_path)
    archive_payload = gate.build_release_final_archive_payload(
        publish_report,
        source_path=publish_path.resolve(),
    )

    assert archive_payload["release_final_archive_status"] == "blocked"
    assert archive_payload["release_final_archive_decision"] == "archive_release_blocker"
    assert archive_payload["release_final_archive_exit_code"] == 1
    assert archive_payload["final_archive_should_publish"] is False
    assert archive_payload["final_archive_requires_manual_action"] is True
    assert archive_payload["final_archive_channel"] == "blocker"
    assert "release_final_archive_blocked" in archive_payload["reason_codes"]


def test_build_release_final_archive_payload_rejects_contract_mismatch(tmp_path: Path):
    gate = _load_ci_workflow_release_final_archive_gate_module()
    publish_payload = _sample_release_final_closure_publish_payload()
    publish_payload["release_final_closure_publish_status"] = "published"
    publish_payload["release_final_closure_publish_decision"] = (
        "announce_release_closed_with_follow_up"
    )
    publish_payload["final_closure_publish_requires_manual_action"] = True
    publish_payload["final_closure_publish_channel"] = "follow_up"

    publish_path = tmp_path / "release_final_closure_publish_mismatch.json"
    publish_path.write_text(json.dumps(publish_payload, indent=2), encoding="utf-8")

    publish_report = gate.load_release_final_closure_publish_report(publish_path)
    archive_payload = gate.build_release_final_archive_payload(
        publish_report,
        source_path=publish_path.resolve(),
    )

    assert archive_payload["release_final_archive_status"] == "contract_failed"
    assert archive_payload["release_final_archive_decision"] == "abort_archive"
    assert archive_payload["release_final_archive_exit_code"] == 1
    assert "final_closure_publish_decision_mismatch" in archive_payload["structural_issues"]
    assert (
        "final_closure_publish_requires_manual_action_mismatch"
        in archive_payload["structural_issues"]
    )
    assert "final_closure_publish_channel_mismatch" in archive_payload["structural_issues"]


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_release_final_archive_gate_module()
    publish_payload = _sample_release_final_closure_publish_payload()
    publish_payload["release_follow_up_final_verdict_status"] = "requires_follow_up"
    publish_payload["release_follow_up_final_verdict_decision"] = "keep_follow_up_open"
    publish_payload["release_follow_up_final_verdict_exit_code"] = 1
    publish_payload["release_final_outcome_status"] = "released_with_follow_up"
    publish_payload["release_final_outcome_decision"] = "ship_with_follow_up_open"
    publish_payload["release_final_outcome_exit_code"] = 1
    publish_payload["release_final_terminal_publish_status"] = "published_with_follow_up"
    publish_payload["release_final_terminal_publish_decision"] = "announce_release_with_follow_up"
    publish_payload["release_final_terminal_publish_exit_code"] = 1
    publish_payload["release_final_handoff_status"] = "completed_with_follow_up"
    publish_payload["release_final_handoff_decision"] = "handoff_release_with_follow_up"
    publish_payload["release_final_handoff_exit_code"] = 1
    publish_payload["release_final_closure_status"] = "closed_with_follow_up"
    publish_payload["release_final_closure_decision"] = "close_with_follow_up"
    publish_payload["release_final_closure_exit_code"] = 1
    publish_payload["release_final_closure_publish_status"] = "published_with_follow_up"
    publish_payload["release_final_closure_publish_decision"] = (
        "announce_release_closed_with_follow_up"
    )
    publish_payload["release_final_closure_publish_exit_code"] = 1
    publish_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    publish_payload["final_closure_publish_should_notify"] = True
    publish_payload["final_closure_publish_requires_manual_action"] = False
    publish_payload["final_closure_publish_channel"] = "follow_up"
    publish_payload["reason_codes"] = ["release_final_closure_publish_with_follow_up"]

    publish_path = tmp_path / "release_final_closure_publish_output.json"
    publish_path.write_text(json.dumps(publish_payload, indent=2), encoding="utf-8")

    publish_report = gate.load_release_final_closure_publish_report(publish_path)
    archive_payload = gate.build_release_final_archive_payload(
        publish_report,
        source_path=publish_path.resolve(),
    )
    outputs = gate.build_github_output_values(
        archive_payload,
        output_json=Path(".claude/reports/linux_unified_gate/ci_workflow_release_final_archive.json"),
        output_markdown=Path(".claude/reports/linux_unified_gate/ci_workflow_release_final_archive.md"),
    )

    assert outputs["workflow_release_final_archive_status"] == "archived_with_follow_up"
    assert (
        outputs["workflow_release_final_archive_decision"]
        == "archive_release_closed_with_follow_up"
    )
    assert outputs["workflow_release_final_archive_exit_code"] == "1"
    assert outputs["workflow_release_final_archive_should_publish"] == "true"
    assert outputs["workflow_release_final_archive_requires_manual_action"] == "false"
    assert outputs["workflow_release_final_archive_channel"] == "follow_up"
    assert outputs["workflow_release_final_archive_follow_up_queue_url"].endswith("/issues/77")
    assert outputs["workflow_release_final_archive_run_id"] == "1234567890"
    assert outputs["workflow_release_final_archive_run_url"].endswith(
        "/actions/runs/1234567890"
    )
    assert outputs["workflow_release_final_archive_report_json"].endswith(
        "ci_workflow_release_final_archive.json"
    )
    assert outputs["workflow_release_final_archive_report_markdown"].endswith(
        "ci_workflow_release_final_archive.md"
    )

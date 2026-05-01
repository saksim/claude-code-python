"""Contract tests for P2-54 Linux CI workflow release final verdict gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_release_final_verdict_gate_module():
    script_path = Path("scripts") / "run_p2_linux_ci_workflow_release_final_verdict_gate.py"
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_release_final_verdict_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_release_final_archive_payload() -> dict:
    return {
        "generated_at": "2026-05-01T00:00:00+00:00",
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
        "release_run_id": 1234567890,
        "release_run_url": "https://github.com/acme/demo/actions/runs/1234567890",
        "follow_up_queue_url": "",
        "final_archive_should_publish": True,
        "final_archive_requires_manual_action": False,
        "final_archive_channel": "release",
        "release_final_archive_summary": (
            "release_final_closure_publish_status=published "
            "release_final_archive_status=archived "
            "release_final_archive_decision=archive_release_closed"
        ),
        "reason_codes": ["release_final_archive_archived"],
        "structural_issues": [],
        "missing_artifacts": [],
        "evidence_manifest": [
            {
                "source": "final_closure_publish",
                "path": "/tmp/ci_workflow_release_final_closure_publish.json",
                "exists": True,
            },
            {
                "source": "final_closure",
                "path": "/tmp/ci_workflow_release_final_closure.json",
                "exists": True,
            },
        ],
    }


def test_build_release_final_verdict_payload_released(tmp_path: Path):
    gate = _load_ci_workflow_release_final_verdict_gate_module()
    archive_payload = _sample_release_final_archive_payload()

    archive_path = tmp_path / "ci_workflow_release_final_archive.json"
    archive_path.write_text(json.dumps(archive_payload, indent=2), encoding="utf-8")

    archive_report = gate.load_release_final_archive_report(archive_path)
    verdict_payload = gate.build_release_final_verdict_payload(
        archive_report,
        source_path=archive_path.resolve(),
    )

    assert verdict_payload["release_final_verdict_status"] == "released"
    assert verdict_payload["release_final_verdict_decision"] == "ship_release"
    assert verdict_payload["release_final_verdict_exit_code"] == 0
    assert verdict_payload["final_verdict_should_ship"] is True
    assert verdict_payload["final_verdict_requires_manual_action"] is False
    assert verdict_payload["final_verdict_channel"] == "release"
    assert "release_final_verdict_released" in verdict_payload["reason_codes"]


def test_build_release_final_verdict_payload_released_with_follow_up(tmp_path: Path):
    gate = _load_ci_workflow_release_final_verdict_gate_module()
    archive_payload = _sample_release_final_archive_payload()
    archive_payload["release_follow_up_final_verdict_status"] = "requires_follow_up"
    archive_payload["release_follow_up_final_verdict_decision"] = "keep_follow_up_open"
    archive_payload["release_follow_up_final_verdict_exit_code"] = 1
    archive_payload["release_final_outcome_status"] = "released_with_follow_up"
    archive_payload["release_final_outcome_decision"] = "ship_with_follow_up_open"
    archive_payload["release_final_outcome_exit_code"] = 1
    archive_payload["release_final_terminal_publish_status"] = "published_with_follow_up"
    archive_payload["release_final_terminal_publish_decision"] = "announce_release_with_follow_up"
    archive_payload["release_final_terminal_publish_exit_code"] = 1
    archive_payload["release_final_handoff_status"] = "completed_with_follow_up"
    archive_payload["release_final_handoff_decision"] = "handoff_release_with_follow_up"
    archive_payload["release_final_handoff_exit_code"] = 1
    archive_payload["release_final_closure_status"] = "closed_with_follow_up"
    archive_payload["release_final_closure_decision"] = "close_with_follow_up"
    archive_payload["release_final_closure_exit_code"] = 1
    archive_payload["release_final_closure_publish_status"] = "published_with_follow_up"
    archive_payload["release_final_closure_publish_decision"] = (
        "announce_release_closed_with_follow_up"
    )
    archive_payload["release_final_closure_publish_exit_code"] = 1
    archive_payload["release_final_archive_status"] = "archived_with_follow_up"
    archive_payload["release_final_archive_decision"] = "archive_release_closed_with_follow_up"
    archive_payload["release_final_archive_exit_code"] = 1
    archive_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    archive_payload["final_archive_should_publish"] = True
    archive_payload["final_archive_requires_manual_action"] = False
    archive_payload["final_archive_channel"] = "follow_up"
    archive_payload["reason_codes"] = ["release_final_archive_archived_with_follow_up"]

    archive_path = tmp_path / "release_final_archive_with_follow_up.json"
    archive_path.write_text(json.dumps(archive_payload, indent=2), encoding="utf-8")

    archive_report = gate.load_release_final_archive_report(archive_path)
    verdict_payload = gate.build_release_final_verdict_payload(
        archive_report,
        source_path=archive_path.resolve(),
    )

    assert verdict_payload["release_final_verdict_status"] == "released_with_follow_up"
    assert verdict_payload["release_final_verdict_decision"] == "ship_release_with_follow_up"
    assert verdict_payload["release_final_verdict_exit_code"] == 1
    assert verdict_payload["final_verdict_should_ship"] is True
    assert verdict_payload["final_verdict_requires_manual_action"] is False
    assert verdict_payload["final_verdict_channel"] == "follow_up"
    assert "release_final_verdict_released_with_follow_up" in verdict_payload["reason_codes"]


def test_build_release_final_verdict_payload_blocked(tmp_path: Path):
    gate = _load_ci_workflow_release_final_verdict_gate_module()
    archive_payload = _sample_release_final_archive_payload()
    archive_payload["release_delivery_final_verdict_status"] = "blocked"
    archive_payload["release_delivery_final_verdict_decision"] = "escalate_blocker"
    archive_payload["release_delivery_final_verdict_exit_code"] = 1
    archive_payload["release_follow_up_final_verdict_status"] = "blocked"
    archive_payload["release_follow_up_final_verdict_decision"] = "escalate_queue_failure"
    archive_payload["release_follow_up_final_verdict_exit_code"] = 1
    archive_payload["release_final_outcome_status"] = "blocked"
    archive_payload["release_final_outcome_decision"] = "escalate_blocker"
    archive_payload["release_final_outcome_exit_code"] = 1
    archive_payload["release_final_terminal_publish_status"] = "blocked"
    archive_payload["release_final_terminal_publish_decision"] = "announce_blocker"
    archive_payload["release_final_terminal_publish_exit_code"] = 1
    archive_payload["release_final_handoff_status"] = "blocked"
    archive_payload["release_final_handoff_decision"] = "handoff_blocker"
    archive_payload["release_final_handoff_exit_code"] = 1
    archive_payload["release_final_closure_status"] = "blocked"
    archive_payload["release_final_closure_decision"] = "close_blocker"
    archive_payload["release_final_closure_exit_code"] = 1
    archive_payload["release_final_closure_publish_status"] = "blocked"
    archive_payload["release_final_closure_publish_decision"] = "announce_release_blocker"
    archive_payload["release_final_closure_publish_exit_code"] = 1
    archive_payload["release_final_archive_status"] = "blocked"
    archive_payload["release_final_archive_decision"] = "archive_release_blocker"
    archive_payload["release_final_archive_exit_code"] = 1
    archive_payload["final_archive_should_publish"] = False
    archive_payload["final_archive_requires_manual_action"] = True
    archive_payload["final_archive_channel"] = "blocker"
    archive_payload["reason_codes"] = ["release_final_archive_blocked"]

    archive_path = tmp_path / "release_final_archive_blocked.json"
    archive_path.write_text(json.dumps(archive_payload, indent=2), encoding="utf-8")

    archive_report = gate.load_release_final_archive_report(archive_path)
    verdict_payload = gate.build_release_final_verdict_payload(
        archive_report,
        source_path=archive_path.resolve(),
    )

    assert verdict_payload["release_final_verdict_status"] == "blocked"
    assert verdict_payload["release_final_verdict_decision"] == "escalate_release_blocker"
    assert verdict_payload["release_final_verdict_exit_code"] == 1
    assert verdict_payload["final_verdict_should_ship"] is False
    assert verdict_payload["final_verdict_requires_manual_action"] is True
    assert verdict_payload["final_verdict_channel"] == "blocker"
    assert "release_final_verdict_blocked" in verdict_payload["reason_codes"]


def test_build_release_final_verdict_payload_rejects_contract_mismatch(tmp_path: Path):
    gate = _load_ci_workflow_release_final_verdict_gate_module()
    archive_payload = _sample_release_final_archive_payload()
    archive_payload["release_final_archive_status"] = "archived"
    archive_payload["release_final_archive_decision"] = "archive_release_closed_with_follow_up"
    archive_payload["final_archive_requires_manual_action"] = True
    archive_payload["final_archive_channel"] = "follow_up"

    archive_path = tmp_path / "release_final_archive_mismatch.json"
    archive_path.write_text(json.dumps(archive_payload, indent=2), encoding="utf-8")

    archive_report = gate.load_release_final_archive_report(archive_path)
    verdict_payload = gate.build_release_final_verdict_payload(
        archive_report,
        source_path=archive_path.resolve(),
    )

    assert verdict_payload["release_final_verdict_status"] == "contract_failed"
    assert verdict_payload["release_final_verdict_decision"] == "abort_verdict"
    assert verdict_payload["release_final_verdict_exit_code"] == 1
    assert "final_archive_decision_mismatch" in verdict_payload["structural_issues"]
    assert (
        "final_archive_requires_manual_action_mismatch"
        in verdict_payload["structural_issues"]
    )
    assert "final_archive_channel_mismatch" in verdict_payload["structural_issues"]


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_release_final_verdict_gate_module()
    archive_payload = _sample_release_final_archive_payload()
    archive_payload["release_follow_up_final_verdict_status"] = "requires_follow_up"
    archive_payload["release_follow_up_final_verdict_decision"] = "keep_follow_up_open"
    archive_payload["release_follow_up_final_verdict_exit_code"] = 1
    archive_payload["release_final_outcome_status"] = "released_with_follow_up"
    archive_payload["release_final_outcome_decision"] = "ship_with_follow_up_open"
    archive_payload["release_final_outcome_exit_code"] = 1
    archive_payload["release_final_terminal_publish_status"] = "published_with_follow_up"
    archive_payload["release_final_terminal_publish_decision"] = "announce_release_with_follow_up"
    archive_payload["release_final_terminal_publish_exit_code"] = 1
    archive_payload["release_final_handoff_status"] = "completed_with_follow_up"
    archive_payload["release_final_handoff_decision"] = "handoff_release_with_follow_up"
    archive_payload["release_final_handoff_exit_code"] = 1
    archive_payload["release_final_closure_status"] = "closed_with_follow_up"
    archive_payload["release_final_closure_decision"] = "close_with_follow_up"
    archive_payload["release_final_closure_exit_code"] = 1
    archive_payload["release_final_closure_publish_status"] = "published_with_follow_up"
    archive_payload["release_final_closure_publish_decision"] = (
        "announce_release_closed_with_follow_up"
    )
    archive_payload["release_final_closure_publish_exit_code"] = 1
    archive_payload["release_final_archive_status"] = "archived_with_follow_up"
    archive_payload["release_final_archive_decision"] = "archive_release_closed_with_follow_up"
    archive_payload["release_final_archive_exit_code"] = 1
    archive_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    archive_payload["final_archive_should_publish"] = True
    archive_payload["final_archive_requires_manual_action"] = False
    archive_payload["final_archive_channel"] = "follow_up"
    archive_payload["reason_codes"] = ["release_final_archive_archived_with_follow_up"]

    archive_path = tmp_path / "release_final_archive_output.json"
    archive_path.write_text(json.dumps(archive_payload, indent=2), encoding="utf-8")

    archive_report = gate.load_release_final_archive_report(archive_path)
    verdict_payload = gate.build_release_final_verdict_payload(
        archive_report,
        source_path=archive_path.resolve(),
    )
    outputs = gate.build_github_output_values(
        verdict_payload,
        output_json=Path(".claude/reports/linux_unified_gate/ci_workflow_release_final_verdict.json"),
        output_markdown=Path(".claude/reports/linux_unified_gate/ci_workflow_release_final_verdict.md"),
    )

    assert outputs["workflow_release_final_verdict_status"] == "released_with_follow_up"
    assert (
        outputs["workflow_release_final_verdict_decision"]
        == "ship_release_with_follow_up"
    )
    assert outputs["workflow_release_final_verdict_exit_code"] == "1"
    assert outputs["workflow_release_final_verdict_should_ship"] == "true"
    assert outputs["workflow_release_final_verdict_requires_manual_action"] == "false"
    assert outputs["workflow_release_final_verdict_channel"] == "follow_up"
    assert outputs["workflow_release_final_verdict_follow_up_queue_url"].endswith("/issues/77")
    assert outputs["workflow_release_final_verdict_run_id"] == "1234567890"
    assert outputs["workflow_release_final_verdict_run_url"].endswith(
        "/actions/runs/1234567890"
    )
    assert outputs["workflow_release_final_verdict_report_json"].endswith(
        "ci_workflow_release_final_verdict.json"
    )
    assert outputs["workflow_release_final_verdict_report_markdown"].endswith(
        "ci_workflow_release_final_verdict.md"
    )

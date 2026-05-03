"""Contract tests for P2-50 Linux CI workflow release final handoff gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_release_final_handoff_gate_module():
    script_path = Path("scripts") / "run_p2_linux_ci_workflow_release_final_handoff_gate.py"
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_release_final_handoff_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_release_final_terminal_publish_payload() -> dict:
    return {
        "generated_at": "2026-05-01T00:00:00+00:00",
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
        "release_run_id": 1234567890,
        "release_run_url": "https://github.com/acme/demo/actions/runs/1234567890",
        "follow_up_queue_url": "",
        "final_should_ship_release": True,
        "final_follow_up_open": False,
        "final_should_page_owner": False,
        "final_outcome_target": "release",
        "release_final_terminal_publish_status": "published",
        "release_final_terminal_publish_decision": "announce_release_closure",
        "release_final_terminal_publish_exit_code": 0,
        "final_terminal_should_notify": True,
        "final_terminal_requires_manual_action": False,
        "final_terminal_channel": "release",
        "release_final_terminal_publish_summary": (
            "release_final_outcome_status=released "
            "release_final_terminal_publish_status=published "
            "release_final_terminal_publish_decision=announce_release_closure"
        ),
        "reason_codes": ["release_final_terminal_published"],
        "structural_issues": [],
        "missing_artifacts": [],
        "evidence_manifest": [
            {"source": "delivery", "path": "/tmp/ci_workflow_release_delivery_final_verdict.json", "exists": True},
            {"source": "follow_up", "path": "/tmp/ci_workflow_release_follow_up_final_verdict.json", "exists": True},
        ],
    }


def test_build_release_final_handoff_payload_completed(tmp_path: Path):
    gate = _load_ci_workflow_release_final_handoff_gate_module()
    final_terminal_payload = _sample_release_final_terminal_publish_payload()

    final_terminal_path = tmp_path / "ci_workflow_release_final_terminal_publish.json"
    final_terminal_path.write_text(json.dumps(final_terminal_payload, indent=2), encoding="utf-8")

    final_terminal_report = gate.load_release_final_terminal_publish_report(final_terminal_path)
    handoff_payload = gate.build_release_final_handoff_payload(
        final_terminal_report,
        source_path=final_terminal_path.resolve(),
    )

    assert handoff_payload["release_final_handoff_status"] == "completed"
    assert handoff_payload["release_final_handoff_decision"] == "handoff_release_closure"
    assert handoff_payload["release_final_handoff_exit_code"] == 0
    assert handoff_payload["final_handoff_should_archive_release"] is True
    assert handoff_payload["final_handoff_keep_follow_up_open"] is False
    assert handoff_payload["final_handoff_should_page_owner"] is False
    assert handoff_payload["final_handoff_target"] == "release"
    assert "release_final_handoff_completed" in handoff_payload["reason_codes"]


def test_build_release_final_handoff_payload_completed_with_follow_up(tmp_path: Path):
    gate = _load_ci_workflow_release_final_handoff_gate_module()
    final_terminal_payload = _sample_release_final_terminal_publish_payload()
    final_terminal_payload["release_follow_up_final_verdict_status"] = "requires_follow_up"
    final_terminal_payload["release_follow_up_final_verdict_decision"] = "keep_follow_up_open"
    final_terminal_payload["release_follow_up_final_verdict_exit_code"] = 1
    final_terminal_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    final_terminal_payload["release_final_outcome_status"] = "released_with_follow_up"
    final_terminal_payload["release_final_outcome_decision"] = "ship_with_follow_up_open"
    final_terminal_payload["release_final_outcome_exit_code"] = 1
    final_terminal_payload["final_should_ship_release"] = True
    final_terminal_payload["final_follow_up_open"] = True
    final_terminal_payload["final_should_page_owner"] = False
    final_terminal_payload["final_outcome_target"] = "follow_up"
    final_terminal_payload["release_final_terminal_publish_status"] = "published_with_follow_up"
    final_terminal_payload["release_final_terminal_publish_decision"] = "announce_release_with_follow_up"
    final_terminal_payload["release_final_terminal_publish_exit_code"] = 1
    final_terminal_payload["final_terminal_should_notify"] = True
    final_terminal_payload["final_terminal_requires_manual_action"] = False
    final_terminal_payload["final_terminal_channel"] = "follow_up"
    final_terminal_payload["reason_codes"] = ["release_final_terminal_published_with_follow_up"]

    final_terminal_path = tmp_path / "release_final_terminal_publish_with_follow_up.json"
    final_terminal_path.write_text(json.dumps(final_terminal_payload, indent=2), encoding="utf-8")

    final_terminal_report = gate.load_release_final_terminal_publish_report(final_terminal_path)
    handoff_payload = gate.build_release_final_handoff_payload(
        final_terminal_report,
        source_path=final_terminal_path.resolve(),
    )

    assert handoff_payload["release_final_handoff_status"] == "completed_with_follow_up"
    assert handoff_payload["release_final_handoff_decision"] == "handoff_release_with_follow_up"
    assert handoff_payload["release_final_handoff_exit_code"] == 1
    assert handoff_payload["final_handoff_should_archive_release"] is True
    assert handoff_payload["final_handoff_keep_follow_up_open"] is True
    assert handoff_payload["final_handoff_should_page_owner"] is False
    assert handoff_payload["final_handoff_target"] == "follow_up"
    assert "release_final_handoff_completed_with_follow_up" in handoff_payload["reason_codes"]


def test_build_release_final_handoff_payload_blocked(tmp_path: Path):
    gate = _load_ci_workflow_release_final_handoff_gate_module()
    final_terminal_payload = _sample_release_final_terminal_publish_payload()
    final_terminal_payload["release_delivery_final_verdict_status"] = "blocked"
    final_terminal_payload["release_delivery_final_verdict_decision"] = "escalate_blocker"
    final_terminal_payload["release_delivery_final_verdict_exit_code"] = 1
    final_terminal_payload["release_follow_up_final_verdict_status"] = "blocked"
    final_terminal_payload["release_follow_up_final_verdict_decision"] = "escalate_queue_failure"
    final_terminal_payload["release_follow_up_final_verdict_exit_code"] = 1
    final_terminal_payload["release_final_outcome_status"] = "blocked"
    final_terminal_payload["release_final_outcome_decision"] = "escalate_blocker"
    final_terminal_payload["release_final_outcome_exit_code"] = 1
    final_terminal_payload["final_should_ship_release"] = False
    final_terminal_payload["final_follow_up_open"] = True
    final_terminal_payload["final_should_page_owner"] = True
    final_terminal_payload["final_outcome_target"] = "blocker"
    final_terminal_payload["release_final_terminal_publish_status"] = "blocked"
    final_terminal_payload["release_final_terminal_publish_decision"] = "announce_blocker"
    final_terminal_payload["release_final_terminal_publish_exit_code"] = 1
    final_terminal_payload["final_terminal_should_notify"] = True
    final_terminal_payload["final_terminal_requires_manual_action"] = True
    final_terminal_payload["final_terminal_channel"] = "blocker"
    final_terminal_payload["reason_codes"] = ["release_final_terminal_blocked"]

    final_terminal_path = tmp_path / "release_final_terminal_publish_blocked.json"
    final_terminal_path.write_text(json.dumps(final_terminal_payload, indent=2), encoding="utf-8")

    final_terminal_report = gate.load_release_final_terminal_publish_report(final_terminal_path)
    handoff_payload = gate.build_release_final_handoff_payload(
        final_terminal_report,
        source_path=final_terminal_path.resolve(),
    )

    assert handoff_payload["release_final_handoff_status"] == "blocked"
    assert handoff_payload["release_final_handoff_decision"] == "handoff_blocker"
    assert handoff_payload["release_final_handoff_exit_code"] == 1
    assert handoff_payload["final_handoff_should_archive_release"] is False
    assert handoff_payload["final_handoff_keep_follow_up_open"] is True
    assert handoff_payload["final_handoff_should_page_owner"] is True
    assert handoff_payload["final_handoff_target"] == "blocker"
    assert "release_final_handoff_blocked" in handoff_payload["reason_codes"]


def test_build_release_final_handoff_payload_rejects_contract_mismatch(tmp_path: Path):
    gate = _load_ci_workflow_release_final_handoff_gate_module()
    final_terminal_payload = _sample_release_final_terminal_publish_payload()
    final_terminal_payload["release_final_terminal_publish_status"] = "published"
    final_terminal_payload["release_final_terminal_publish_decision"] = "announce_release_with_follow_up"
    final_terminal_payload["final_follow_up_open"] = True
    final_terminal_payload["final_terminal_channel"] = "follow_up"

    final_terminal_path = tmp_path / "release_final_terminal_publish_mismatch.json"
    final_terminal_path.write_text(json.dumps(final_terminal_payload, indent=2), encoding="utf-8")

    final_terminal_report = gate.load_release_final_terminal_publish_report(final_terminal_path)
    handoff_payload = gate.build_release_final_handoff_payload(
        final_terminal_report,
        source_path=final_terminal_path.resolve(),
    )

    assert handoff_payload["release_final_handoff_status"] == "contract_failed"
    assert handoff_payload["release_final_handoff_decision"] == "abort_handoff"
    assert handoff_payload["release_final_handoff_exit_code"] == 1
    assert "final_terminal_decision_mismatch" in handoff_payload["structural_issues"]
    assert "final_follow_up_open_mismatch" in handoff_payload["structural_issues"]
    assert "final_terminal_channel_mismatch" in handoff_payload["structural_issues"]


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_release_final_handoff_gate_module()
    final_terminal_payload = _sample_release_final_terminal_publish_payload()
    final_terminal_payload["release_follow_up_final_verdict_status"] = "requires_follow_up"
    final_terminal_payload["release_follow_up_final_verdict_decision"] = "keep_follow_up_open"
    final_terminal_payload["release_follow_up_final_verdict_exit_code"] = 1
    final_terminal_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    final_terminal_payload["release_final_outcome_status"] = "released_with_follow_up"
    final_terminal_payload["release_final_outcome_decision"] = "ship_with_follow_up_open"
    final_terminal_payload["release_final_outcome_exit_code"] = 1
    final_terminal_payload["final_should_ship_release"] = True
    final_terminal_payload["final_follow_up_open"] = True
    final_terminal_payload["final_should_page_owner"] = False
    final_terminal_payload["final_outcome_target"] = "follow_up"
    final_terminal_payload["release_final_terminal_publish_status"] = "published_with_follow_up"
    final_terminal_payload["release_final_terminal_publish_decision"] = "announce_release_with_follow_up"
    final_terminal_payload["release_final_terminal_publish_exit_code"] = 1
    final_terminal_payload["final_terminal_should_notify"] = True
    final_terminal_payload["final_terminal_requires_manual_action"] = False
    final_terminal_payload["final_terminal_channel"] = "follow_up"
    final_terminal_payload["reason_codes"] = ["release_final_terminal_published_with_follow_up"]

    final_terminal_path = tmp_path / "release_final_terminal_publish_output.json"
    final_terminal_path.write_text(json.dumps(final_terminal_payload, indent=2), encoding="utf-8")

    final_terminal_report = gate.load_release_final_terminal_publish_report(final_terminal_path)
    handoff_payload = gate.build_release_final_handoff_payload(
        final_terminal_report,
        source_path=final_terminal_path.resolve(),
    )
    outputs = gate.build_github_output_values(
        handoff_payload,
        output_json=Path(".claude/reports/linux_unified_gate/ci_workflow_release_final_handoff.json"),
        output_markdown=Path(".claude/reports/linux_unified_gate/ci_workflow_release_final_handoff.md"),
    )

    assert outputs["workflow_release_final_handoff_status"] == "completed_with_follow_up"
    assert (
        outputs["workflow_release_final_handoff_decision"]
        == "handoff_release_with_follow_up"
    )
    assert outputs["workflow_release_final_handoff_exit_code"] == "1"
    assert outputs["workflow_release_final_handoff_should_archive_release"] == "true"
    assert outputs["workflow_release_final_handoff_keep_follow_up_open"] == "true"
    assert outputs["workflow_release_final_handoff_should_page_owner"] == "false"
    assert outputs["workflow_release_final_handoff_target"] == "follow_up"
    assert outputs["workflow_release_final_handoff_follow_up_queue_url"].endswith("/issues/77")
    assert outputs["workflow_release_final_handoff_run_id"] == "1234567890"
    assert outputs["workflow_release_final_handoff_run_url"].endswith("/actions/runs/1234567890")
    assert outputs["workflow_release_final_handoff_report_json"].endswith(
        "ci_workflow_release_final_handoff.json"
    )
    assert outputs["workflow_release_final_handoff_report_markdown"].endswith(
        "ci_workflow_release_final_handoff.md"
    )

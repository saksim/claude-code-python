"""Contract tests for P2-55 Linux CI workflow release final verdict publish gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_ci_workflow_release_final_verdict_publish_gate_module():
    script_path = (
        Path("scripts") / "run_p2_linux_ci_workflow_release_final_verdict_publish_gate.py"
    )
    spec = importlib.util.spec_from_file_location(
        "p2_linux_ci_workflow_release_final_verdict_publish_gate",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_release_final_verdict_payload() -> dict:
    return {
        "generated_at": "2026-05-01T00:00:00+00:00",
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
        "release_run_id": 1234567890,
        "release_run_url": "https://github.com/acme/demo/actions/runs/1234567890",
        "follow_up_queue_url": "",
        "final_verdict_should_ship": True,
        "final_verdict_requires_manual_action": False,
        "final_verdict_channel": "release",
        "release_final_verdict_status": "released",
        "release_final_verdict_decision": "ship_release",
        "release_final_verdict_exit_code": 0,
        "release_final_verdict_summary": (
            "release_final_archive_status=archived "
            "release_final_verdict_status=released "
            "release_final_verdict_decision=ship_release"
        ),
        "reason_codes": ["release_final_verdict_released"],
        "structural_issues": [],
        "missing_artifacts": [],
        "evidence_manifest": [
            {
                "source": "final_archive",
                "path": "/tmp/ci_workflow_release_final_archive.json",
                "exists": True,
            },
            {
                "source": "final_closure_publish",
                "path": "/tmp/ci_workflow_release_final_closure_publish.json",
                "exists": True,
            },
        ],
    }


def test_build_release_final_verdict_publish_payload_published(tmp_path: Path):
    gate = _load_ci_workflow_release_final_verdict_publish_gate_module()
    verdict_payload = _sample_release_final_verdict_payload()

    verdict_path = tmp_path / "ci_workflow_release_final_verdict.json"
    verdict_path.write_text(json.dumps(verdict_payload, indent=2), encoding="utf-8")

    verdict_report = gate.load_release_final_verdict_report(verdict_path)
    publish_payload = gate.build_release_final_verdict_publish_payload(
        verdict_report,
        source_path=verdict_path.resolve(),
    )

    assert publish_payload["release_final_verdict_publish_status"] == "published"
    assert publish_payload["release_final_verdict_publish_decision"] == "announce_release_shipped"
    assert publish_payload["release_final_verdict_publish_exit_code"] == 0
    assert publish_payload["final_verdict_publish_should_notify"] is True
    assert publish_payload["final_verdict_publish_requires_manual_action"] is False
    assert publish_payload["final_verdict_publish_channel"] == "release"
    assert "release_final_verdict_publish_published" in publish_payload["reason_codes"]


def test_build_release_final_verdict_publish_payload_published_with_follow_up(tmp_path: Path):
    gate = _load_ci_workflow_release_final_verdict_publish_gate_module()
    verdict_payload = _sample_release_final_verdict_payload()
    verdict_payload["release_follow_up_final_verdict_status"] = "requires_follow_up"
    verdict_payload["release_follow_up_final_verdict_decision"] = "keep_follow_up_open"
    verdict_payload["release_follow_up_final_verdict_exit_code"] = 1
    verdict_payload["release_final_outcome_status"] = "released_with_follow_up"
    verdict_payload["release_final_outcome_decision"] = "ship_with_follow_up_open"
    verdict_payload["release_final_outcome_exit_code"] = 1
    verdict_payload["release_final_terminal_publish_status"] = "published_with_follow_up"
    verdict_payload["release_final_terminal_publish_decision"] = "announce_release_with_follow_up"
    verdict_payload["release_final_terminal_publish_exit_code"] = 1
    verdict_payload["release_final_handoff_status"] = "completed_with_follow_up"
    verdict_payload["release_final_handoff_decision"] = "handoff_release_with_follow_up"
    verdict_payload["release_final_handoff_exit_code"] = 1
    verdict_payload["release_final_closure_status"] = "closed_with_follow_up"
    verdict_payload["release_final_closure_decision"] = "close_with_follow_up"
    verdict_payload["release_final_closure_exit_code"] = 1
    verdict_payload["release_final_closure_publish_status"] = "published_with_follow_up"
    verdict_payload["release_final_closure_publish_decision"] = (
        "announce_release_closed_with_follow_up"
    )
    verdict_payload["release_final_closure_publish_exit_code"] = 1
    verdict_payload["release_final_archive_status"] = "archived_with_follow_up"
    verdict_payload["release_final_archive_decision"] = "archive_release_closed_with_follow_up"
    verdict_payload["release_final_archive_exit_code"] = 1
    verdict_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    verdict_payload["final_verdict_should_ship"] = True
    verdict_payload["final_verdict_requires_manual_action"] = False
    verdict_payload["final_verdict_channel"] = "follow_up"
    verdict_payload["release_final_verdict_status"] = "released_with_follow_up"
    verdict_payload["release_final_verdict_decision"] = "ship_release_with_follow_up"
    verdict_payload["release_final_verdict_exit_code"] = 1
    verdict_payload["reason_codes"] = ["release_final_verdict_released_with_follow_up"]

    verdict_path = tmp_path / "release_final_verdict_with_follow_up.json"
    verdict_path.write_text(json.dumps(verdict_payload, indent=2), encoding="utf-8")

    verdict_report = gate.load_release_final_verdict_report(verdict_path)
    publish_payload = gate.build_release_final_verdict_publish_payload(
        verdict_report,
        source_path=verdict_path.resolve(),
    )

    assert publish_payload["release_final_verdict_publish_status"] == "published_with_follow_up"
    assert (
        publish_payload["release_final_verdict_publish_decision"]
        == "announce_release_shipped_with_follow_up"
    )
    assert publish_payload["release_final_verdict_publish_exit_code"] == 1
    assert publish_payload["final_verdict_publish_should_notify"] is True
    assert publish_payload["final_verdict_publish_requires_manual_action"] is False
    assert publish_payload["final_verdict_publish_channel"] == "follow_up"
    assert "release_final_verdict_publish_with_follow_up" in publish_payload["reason_codes"]


def test_build_release_final_verdict_publish_payload_blocked(tmp_path: Path):
    gate = _load_ci_workflow_release_final_verdict_publish_gate_module()
    verdict_payload = _sample_release_final_verdict_payload()
    verdict_payload["release_delivery_final_verdict_status"] = "blocked"
    verdict_payload["release_delivery_final_verdict_decision"] = "escalate_blocker"
    verdict_payload["release_delivery_final_verdict_exit_code"] = 1
    verdict_payload["release_follow_up_final_verdict_status"] = "blocked"
    verdict_payload["release_follow_up_final_verdict_decision"] = "escalate_queue_failure"
    verdict_payload["release_follow_up_final_verdict_exit_code"] = 1
    verdict_payload["release_final_outcome_status"] = "blocked"
    verdict_payload["release_final_outcome_decision"] = "escalate_blocker"
    verdict_payload["release_final_outcome_exit_code"] = 1
    verdict_payload["release_final_terminal_publish_status"] = "blocked"
    verdict_payload["release_final_terminal_publish_decision"] = "announce_blocker"
    verdict_payload["release_final_terminal_publish_exit_code"] = 1
    verdict_payload["release_final_handoff_status"] = "blocked"
    verdict_payload["release_final_handoff_decision"] = "handoff_blocker"
    verdict_payload["release_final_handoff_exit_code"] = 1
    verdict_payload["release_final_closure_status"] = "blocked"
    verdict_payload["release_final_closure_decision"] = "close_blocker"
    verdict_payload["release_final_closure_exit_code"] = 1
    verdict_payload["release_final_closure_publish_status"] = "blocked"
    verdict_payload["release_final_closure_publish_decision"] = "announce_release_blocker"
    verdict_payload["release_final_closure_publish_exit_code"] = 1
    verdict_payload["release_final_archive_status"] = "blocked"
    verdict_payload["release_final_archive_decision"] = "archive_release_blocker"
    verdict_payload["release_final_archive_exit_code"] = 1
    verdict_payload["final_verdict_should_ship"] = False
    verdict_payload["final_verdict_requires_manual_action"] = True
    verdict_payload["final_verdict_channel"] = "blocker"
    verdict_payload["release_final_verdict_status"] = "blocked"
    verdict_payload["release_final_verdict_decision"] = "escalate_release_blocker"
    verdict_payload["release_final_verdict_exit_code"] = 1
    verdict_payload["reason_codes"] = ["release_final_verdict_blocked"]

    verdict_path = tmp_path / "release_final_verdict_blocked.json"
    verdict_path.write_text(json.dumps(verdict_payload, indent=2), encoding="utf-8")

    verdict_report = gate.load_release_final_verdict_report(verdict_path)
    publish_payload = gate.build_release_final_verdict_publish_payload(
        verdict_report,
        source_path=verdict_path.resolve(),
    )

    assert publish_payload["release_final_verdict_publish_status"] == "blocked"
    assert publish_payload["release_final_verdict_publish_decision"] == "announce_release_blocker"
    assert publish_payload["release_final_verdict_publish_exit_code"] == 1
    assert publish_payload["final_verdict_publish_should_notify"] is True
    assert publish_payload["final_verdict_publish_requires_manual_action"] is True
    assert publish_payload["final_verdict_publish_channel"] == "blocker"
    assert "release_final_verdict_publish_blocked" in publish_payload["reason_codes"]


def test_build_release_final_verdict_publish_payload_rejects_contract_mismatch(
    tmp_path: Path,
):
    gate = _load_ci_workflow_release_final_verdict_publish_gate_module()
    verdict_payload = _sample_release_final_verdict_payload()
    verdict_payload["release_final_verdict_status"] = "released"
    verdict_payload["release_final_verdict_decision"] = "ship_release_with_follow_up"
    verdict_payload["final_verdict_requires_manual_action"] = True
    verdict_payload["final_verdict_channel"] = "follow_up"

    verdict_path = tmp_path / "release_final_verdict_mismatch.json"
    verdict_path.write_text(json.dumps(verdict_payload, indent=2), encoding="utf-8")

    verdict_report = gate.load_release_final_verdict_report(verdict_path)
    publish_payload = gate.build_release_final_verdict_publish_payload(
        verdict_report,
        source_path=verdict_path.resolve(),
    )

    assert publish_payload["release_final_verdict_publish_status"] == "contract_failed"
    assert publish_payload["release_final_verdict_publish_decision"] == "abort_publish"
    assert publish_payload["release_final_verdict_publish_exit_code"] == 1
    assert "final_verdict_decision_mismatch" in publish_payload["structural_issues"]
    assert "final_verdict_requires_manual_action_mismatch" in publish_payload["structural_issues"]
    assert "final_verdict_channel_mismatch" in publish_payload["structural_issues"]


def test_build_github_output_values_contract(tmp_path: Path):
    gate = _load_ci_workflow_release_final_verdict_publish_gate_module()
    verdict_payload = _sample_release_final_verdict_payload()
    verdict_payload["release_follow_up_final_verdict_status"] = "requires_follow_up"
    verdict_payload["release_follow_up_final_verdict_decision"] = "keep_follow_up_open"
    verdict_payload["release_follow_up_final_verdict_exit_code"] = 1
    verdict_payload["release_final_outcome_status"] = "released_with_follow_up"
    verdict_payload["release_final_outcome_decision"] = "ship_with_follow_up_open"
    verdict_payload["release_final_outcome_exit_code"] = 1
    verdict_payload["release_final_terminal_publish_status"] = "published_with_follow_up"
    verdict_payload["release_final_terminal_publish_decision"] = "announce_release_with_follow_up"
    verdict_payload["release_final_terminal_publish_exit_code"] = 1
    verdict_payload["release_final_handoff_status"] = "completed_with_follow_up"
    verdict_payload["release_final_handoff_decision"] = "handoff_release_with_follow_up"
    verdict_payload["release_final_handoff_exit_code"] = 1
    verdict_payload["release_final_closure_status"] = "closed_with_follow_up"
    verdict_payload["release_final_closure_decision"] = "close_with_follow_up"
    verdict_payload["release_final_closure_exit_code"] = 1
    verdict_payload["release_final_closure_publish_status"] = "published_with_follow_up"
    verdict_payload["release_final_closure_publish_decision"] = (
        "announce_release_closed_with_follow_up"
    )
    verdict_payload["release_final_closure_publish_exit_code"] = 1
    verdict_payload["release_final_archive_status"] = "archived_with_follow_up"
    verdict_payload["release_final_archive_decision"] = "archive_release_closed_with_follow_up"
    verdict_payload["release_final_archive_exit_code"] = 1
    verdict_payload["follow_up_queue_url"] = "https://github.com/acme/demo/issues/77"
    verdict_payload["final_verdict_should_ship"] = True
    verdict_payload["final_verdict_requires_manual_action"] = False
    verdict_payload["final_verdict_channel"] = "follow_up"
    verdict_payload["release_final_verdict_status"] = "released_with_follow_up"
    verdict_payload["release_final_verdict_decision"] = "ship_release_with_follow_up"
    verdict_payload["release_final_verdict_exit_code"] = 1
    verdict_payload["reason_codes"] = ["release_final_verdict_released_with_follow_up"]

    verdict_path = tmp_path / "release_final_verdict_output.json"
    verdict_path.write_text(json.dumps(verdict_payload, indent=2), encoding="utf-8")

    verdict_report = gate.load_release_final_verdict_report(verdict_path)
    publish_payload = gate.build_release_final_verdict_publish_payload(
        verdict_report,
        source_path=verdict_path.resolve(),
    )
    outputs = gate.build_github_output_values(
        publish_payload,
        output_json=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_final_verdict_publish.json"
        ),
        output_markdown=Path(
            ".claude/reports/linux_unified_gate/ci_workflow_release_final_verdict_publish.md"
        ),
    )

    assert outputs["workflow_release_final_verdict_publish_status"] == "published_with_follow_up"
    assert (
        outputs["workflow_release_final_verdict_publish_decision"]
        == "announce_release_shipped_with_follow_up"
    )
    assert outputs["workflow_release_final_verdict_publish_exit_code"] == "1"
    assert outputs["workflow_release_final_verdict_publish_should_notify"] == "true"
    assert outputs["workflow_release_final_verdict_publish_requires_manual_action"] == "false"
    assert outputs["workflow_release_final_verdict_publish_channel"] == "follow_up"
    assert outputs["workflow_release_final_verdict_publish_follow_up_queue_url"].endswith(
        "/issues/77"
    )
    assert outputs["workflow_release_final_verdict_publish_run_id"] == "1234567890"
    assert outputs["workflow_release_final_verdict_publish_run_url"].endswith(
        "/actions/runs/1234567890"
    )
    assert outputs["workflow_release_final_verdict_publish_report_json"].endswith(
        "ci_workflow_release_final_verdict_publish.json"
    )
    assert outputs["workflow_release_final_verdict_publish_report_markdown"].endswith(
        "ci_workflow_release_final_verdict_publish.md"
    )

